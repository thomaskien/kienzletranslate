import json
import os
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from .audio import MAX_BYTES, inspect_wav
from .process_model import ProcessModel
from .lid import LanguageDetector
from .service import Service, ServiceError

LANGUAGES = json.loads(Path(__file__).with_name("languages.json").read_text())
CODES = {row["code"] for row in LANGUAGES}


def create_app(config=None, model=None):
    if config is None:
        config = json.loads(Path(os.environ.get("KIENZLE_CONFIG", "/etc/kienzletranslate/config.json")).read_text())
    token = config["backend_token"]
    if len(token) < 32:
        raise RuntimeError("Backend token must contain at least 32 characters")
    service = Service(model or ProcessModel(config["model_path"], config.get("model_min_free_mib", 8192)),
                      config=config, detector=LanguageDetector(config.get("lid_python", "/opt/kienzletranslate/lid-venv/bin/python"),
                      config.get("lid_model_path", "/var/lib/kienzletranslate/lid-model")))

    @asynccontextmanager
    async def lifespan(app):
        if config.get("model_autoload", False):
            service.lifecycle("load")
        yield
        service.close()

    async def authorize(request: Request):
        if not secrets.compare_digest(request.headers.get("authorization", ""), "Bearer " + token):
            raise HTTPException(401, "Unauthorized")

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan,
                  dependencies=[Depends(authorize)])
    app.state.service = service

    @app.exception_handler(ServiceError)
    async def service_error(request, exc):
        return JSONResponse({"error": exc.message, "code": exc.code}, status_code=exc.status)

    @app.middleware("http")
    async def no_store(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    def identifiers(session, uid=None):
        if not re.fullmatch(r"[0-9a-f]{32}", session):
            raise HTTPException(400, "Invalid session")
        if uid is not None and not re.fullmatch(r"[0-9a-fA-F-]{36}", uid):
            raise HTTPException(400, "Invalid utterance id")

    @app.get("/health")
    def health():
        return service.health()

    @app.post("/model/{action}")
    def lifecycle(action: str):
        if action not in {"load", "unload"}:
            raise HTTPException(404)
        return service.lifecycle(action)

    @app.post("/sessions/{session}/heartbeat")
    async def heartbeat(session: str, request: Request):
        identifiers(session)
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 1024:
                raise HTTPException(413, "Too large")
        try:
            data = json.loads(body)
            client = data["client"]
            if not isinstance(client, str) or not re.fullmatch(r"[a-f0-9]{32}", client):
                raise ValueError()
            if any(type(data.get(k, False)) is not bool for k in ("active", "activity", "recording")):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise HTTPException(400, "Invalid heartbeat") from None
        return service.heartbeat(session, client, data.get("active", True), data.get("activity", False), data.get("recording", False))

    @app.post("/sessions/{session}/utterances", status_code=202)
    async def submit(session: str, request: Request, utterance_id: str, source_lang: str,
                     target_lang: str, speaker_side: str, tts: bool = False, generation: int = 0):
        identifiers(session, utterance_id)
        if (source_lang not in CODES and not (source_lang == "auto" and speaker_side == "top")) or target_lang not in CODES or speaker_side not in {"top", "bottom"}:
            raise HTTPException(400, "Unsupported language or speaker")
        content = bytearray()
        async for chunk in request.stream():
            if len(content) + len(chunk) > MAX_BYTES:
                raise HTTPException(413, "Recording too large")
            content.extend(chunk)
        data = bytes(content)
        try:
            inspect_wav(data)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        return service.submit(session, utterance_id, data, source_lang, target_lang, tts, generation)

    @app.get("/sessions/{session}/utterances/{uid}")
    def result(session: str, uid: str):
        identifiers(session, uid)
        return service.result(session, uid)

    @app.get("/sessions/{session}/audio/{uid}")
    def audio(session: str, uid: str):
        identifiers(session, uid)
        return Response(service.result(session, uid, audio=True), media_type="audio/wav")

    @app.delete("/sessions/{session}")
    def clear(session: str):
        identifiers(session)
        service.clear(session)
        return {"ok": True}

    return app
