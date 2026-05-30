from __future__ import annotations

import json
import os

import azure.functions as func

from chronicle_models import ArtifactUpsert, LogAppend, SessionUpdate
from chronicle_storage import get_storage, health_payload

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _json_response(payload: object, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
    )


def _parse_json(req: func.HttpRequest) -> dict:
    try:
        return req.get_json()
    except ValueError as e:
        raise ValueError("invalid json") from e


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    kind = (os.getenv("CHRONICLE_STORAGE") or "file").strip().lower()
    return _json_response(health_payload(kind))


@app.route(route="sessions", methods=["GET"])
def sessions(req: func.HttpRequest) -> func.HttpResponse:
    storage = get_storage()
    return _json_response({"items": storage.list_sessions()})


@app.route(route="session/update", methods=["POST"])
def session_update(req: func.HttpRequest) -> func.HttpResponse:
    storage = get_storage()
    payload = _parse_json(req)
    update = SessionUpdate.from_payload(payload)
    saved = storage.upsert_session(update)
    return _json_response({"ok": True, "item": saved})


@app.route(route="log/append", methods=["POST"])
def log_append(req: func.HttpRequest) -> func.HttpResponse:
    storage = get_storage()
    payload = _parse_json(req)
    item = LogAppend.from_payload(payload)
    saved = storage.append_log(item)
    return _json_response({"ok": True, "item": saved})


# Artifact API is a placeholder in this scaffold. Data model exists; storage wiring comes next.
@app.route(route="artifacts", methods=["GET"])
def artifacts(req: func.HttpRequest) -> func.HttpResponse:
    storage = get_storage()
    return _json_response({"items": storage.list_artifacts()})

