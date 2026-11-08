"""Small bounded serial scheduler. All conversation data has a RAM-only lifetime."""
import logging
import queue
import threading
import time

LOG = logging.getLogger("kienzletranslate")


class ServiceError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


class Service:
    def __init__(self, model, ttl=600):
        self.model = model
        self.ttl = ttl
        self.jobs = {}
        self.lock = threading.RLock()
        self.queue = queue.Queue(maxsize=8)
        self.busy = False
        self.closed = False
        self.thread = threading.Thread(target=self._work, daemon=True)
        self.thread.start()

    def _expire(self):
        cutoff = time.monotonic() - self.ttl
        for key in list(self.jobs):
            if self.jobs[key]["created"] < cutoff:
                del self.jobs[key]

    def health(self):
        with self.lock:
            self._expire()
            return {"state": self.model.state, "error": self.model.error,
                    "busy": self.busy, "queued": self.queue.qsize()}

    def lifecycle(self, action):
        with self.lock:
            if self.busy or not self.queue.empty():
                raise ServiceError(409, "Das Modell bearbeitet gerade eine Anfrage. Bitte kurz warten.")
            if action == "load" and self.model.state == "ready":
                return self.health()
            if action == "unload" and self.model.state == "unloaded":
                return self.health()
            self.busy = True
            self.model.state = "loading" if action == "load" else "unloading"
            self.queue.put_nowait((action, None))
            return self.health()

    def submit(self, session, uid, data, source, target, tts, generation=0):
        with self.lock:
            self._expire()
            if self.model.state == "unloading":
                raise ServiceError(409, "Modell wird entladen. Bitte erneut versuchen.")
            key = (session, uid)
            if key in self.jobs:
                raise ServiceError(409, "Diese Aufnahme wurde bereits übermittelt.")
            if generation and any(k[0] == session and j.get("generation", 0) >= generation for k, j in self.jobs.items()):
                raise ServiceError(409, "Diese Aufnahme wurde bereits durch eine neuere ersetzt.")
            if self.queue.full() or len(self.jobs) >= 64:
                raise ServiceError(429, "Warteschlange ist voll. Bitte kurz warten.")
            # Latest utterance wins within this client; another client is unaffected.
            for old_key in list(self.jobs):
                if old_key[0] == session:
                    del self.jobs[old_key]
            self.jobs[key] = {"id": uid, "status": "queued", "created": time.monotonic(),
                              "input": data, "source": source, "target": target, "tts": tts, "generation": generation}
            self.queue.put_nowait(("translate", key))
            return {"id": uid, "status": "queued"}

    def result(self, session, uid, audio=False):
        with self.lock:
            self._expire()
            job = self.jobs.get((session, uid))
            if job is None:
                raise ServiceError(404, "Ergebnis ist abgelaufen oder wurde ersetzt.")
            if audio:
                if not job.get("audio"):
                    raise ServiceError(404, "Keine Sprachausgabe vorhanden.")
                return job["audio"]
            return {k: v for k, v in job.items() if k not in
                    {"input", "audio", "created", "source", "target", "tts"}}

    def clear(self, session):
        with self.lock:
            for key in list(self.jobs):
                if key[0] == session:
                    del self.jobs[key]

    def _work(self):
        while not self.closed:
            try:
                action, key = self.queue.get(timeout=2)
            except queue.Empty:
                with self.lock:
                    self._expire()
                continue
            job = None
            try:
                with self.lock:
                    if action == "translate":
                        job = self.jobs.get(key)
                        if job is None:
                            continue
                        job["status"] = "processing"
                    self.busy = True
                if action == "load":
                    self.model.load()
                elif action == "unload":
                    self.model.unload()
                else:
                    queued_seconds = time.monotonic() - job["created"]
                    result, audio = self.model.translate(job["input"], job["source"], job["target"], job["tts"])
                    result.setdefault("metrics", {})["queue_seconds"] = round(queued_seconds, 3)
                    with self.lock:
                        if self.jobs.get(key) is job:
                            job.update(result, status="complete", audio=audio)
                    del result, audio
            except Exception as exc:
                # Exception messages/tracebacks can contain user text: log the type only.
                LOG.error("operation=%s error_type=%s", action, type(exc).__name__)
                with self.lock:
                    if job is not None and self.jobs.get(key) is job:
                        job.update(status="error", error="Verarbeitung fehlgeschlagen. Modellstatus und GPU-Speicher prüfen.")
                    if action in ("load", "unload"):
                        self.model.state = "error"
                        self.model.error = "Modelloperation fehlgeschlagen. Bitte Serverstatus prüfen."
            finally:
                if job is not None:
                    job.pop("input", None)
                job = None
                with self.lock:
                    self.busy = False
                self.queue.task_done()

    def close(self):
        self.closed = True
        with self.lock:
            self.jobs.clear()
