"""Small bounded serial scheduler. All conversation data has a RAM-only lifetime."""
import logging
import queue
import threading
import time

LOG = logging.getLogger("kienzletranslate")


class ServiceError(Exception):
    def __init__(self, status, message, code="service_error"):
        self.status, self.message, self.code = status, message, code


class Service:
    def __init__(self, model, ttl=600, config=None, detector=None, clock=time.monotonic):
        self.model = model
        self.ttl = ttl
        self.config = config or {}
        self.detector = detector
        self.clock = clock
        self.clients = {}
        self.last_use = self.clock()
        self.idle_reason = None
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
                    "busy": self.busy, "queued": self.queue.qsize(),
                    "error_code": getattr(self.model, "error_code", None),
                    "idle_reason": self.idle_reason}

    def heartbeat(self, session, client, active=True, activity=False, recording=False):
        with self.lock:
            now = self.clock()
            key = (session, client)
            for stale in list(self.clients):
                if now - self.clients[stale]["seen"] > max(600, self.config.get("model_disconnect_seconds", 90)):
                    del self.clients[stale]
            if key not in self.clients and len(self.clients) >= 128:
                raise ServiceError(429, "Zu viele aktive Geräte.")
            presence = now if active else self.clients.get(key, {}).get("presence", self.last_use)
            self.clients[key] = {"seen": now, "presence": presence, "active": active, "recording": recording and active}
            if active and activity:
                self.last_use = now
                self.idle_reason = None
                if (self.config.get("model_load_on_use", True) and not self.busy and self.queue.empty()
                        and self.model.state in ("unloaded", "error")):
                    self.lifecycle("load")
            return self.health()

    def maintenance(self):
        with self.lock:
            if self.busy or not self.queue.empty() or not self.config.get("model_auto_unload", True):
                return
            now = self.clock()
            disconnect = self.config.get("model_disconnect_seconds", 90)
            live = [c for c in self.clients.values() if c["active"] and now - c["seen"] < disconnect]
            if any(c["recording"] for c in live):
                return
            last_seen = max([self.last_use] + [c["presence"] for c in self.clients.values()])
            reason = None
            if not live and now - last_seen >= disconnect:
                reason = "disconnected"
            elif now - self.last_use >= self.config.get("model_idle_seconds", 300):
                reason = "inactive"
            if reason and self.model.state == "ready":
                self.idle_reason = reason
                self.lifecycle("unload")
            elif reason and self.detector:
                self.detector.close()

    def lifecycle(self, action):
        with self.lock:
            disconnect = self.config.get("model_disconnect_seconds", 90)
            recording = any(c["active"] and c["recording"] and self.clock() - c["seen"] < disconnect
                            for c in self.clients.values())
            if self.busy or not self.queue.empty() or (action == "unload" and recording):
                raise ServiceError(409, "Das Modell bearbeitet gerade eine Anfrage. Bitte kurz warten.")
            if action == "load" and self.model.state == "ready":
                return self.health()
            if action == "unload" and self.model.state == "unloaded":
                return self.health()
            if action == "load":
                self.last_use = self.clock()
                self.idle_reason = None
            self.busy = True
            self.model.state = "loading" if action == "load" else "unloading"
            self.queue.put_nowait((action, None))
            return self.health()

    def submit(self, session, uid, data, source, target, tts, generation=0):
        with self.lock:
            self._expire()
            if self.model.state == "unloading":
                raise ServiceError(409, "Modell wird entladen. Bitte erneut versuchen.")
            if self.model.state in ("unloaded", "error") and not self.config.get("model_load_on_use", True):
                raise ServiceError(409, "Modell bitte in den Einstellungen laden.", "model_not_ready")
            self.last_use = self.clock()
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
            for key in list(self.clients):
                if key[0] == session:
                    del self.clients[key]
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
                self.maintenance()
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
                    if self.detector:
                        self.detector.close()
                else:
                    queued_seconds = time.monotonic() - job["created"]
                    detection = None
                    if job["source"] == "auto":
                        detection = self.detector.detect(job["input"]) if self.detector else {"accepted": False, "reason": "unavailable"}
                        with self.lock:
                            if self.jobs.get(key) is not job:
                                continue
                            job["detection"] = detection
                            if not detection.get("accepted"):
                                job.update(status="language_required", error_code="language_required")
                                continue
                        source = detection["language"]
                    else:
                        source = job["source"]
                    result, audio = self.model.translate(job["input"], source, job["target"], job["tts"])
                    if detection:
                        result["detection"] = detection
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
                        job.update(status="error", error="Verarbeitung fehlgeschlagen. Modellstatus und GPU-Speicher prüfen.", error_code=getattr(exc, "code", "model_error"))
                    if action in ("load", "unload"):
                        self.model.state = "error"
                        self.model.error = "Modelloperation fehlgeschlagen. Bitte Serverstatus prüfen."
            finally:
                if job is not None:
                    job.pop("input", None)
                job = None
                with self.lock:
                    self.busy = False
                    self.last_use = self.clock()
                self.queue.task_done()

    def close(self):
        self.closed = True
        with self.lock:
            self.jobs.clear()
            self.clients.clear()
        self.thread.join(timeout=185)
        self.model.unload()
        if self.detector:
            self.detector.close()
