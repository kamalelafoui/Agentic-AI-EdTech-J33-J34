# -*- coding: utf-8 -*-
"""Implémentation minimale et lisible du protocole A2A (JSON-RPC 2.0).

Chaque agent expose :
- GET /.well-known/agent.json   → AgentCard
- POST /                          → message/send, tasks/get
- GET /health                     → état du service
- POST /run                       → raccourci REST pour le dashboard
"""
from __future__ import annotations

import json
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import a2a_core  # noqa: E402

TASKS: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _extract_text(message: dict[str, Any]) -> str:
    parts = message.get("parts", []) if isinstance(message, dict) else []
    texts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("kind") == "text"]
    return "\n".join(t for t in texts if t).strip()


def _task_from_result(task_id: str, context_id: str, result: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    task = {
        "kind": "task",
        "id": task_id,
        "contextId": context_id,
        "status": {"state": "completed", "timestamp": _now()},
        "artifacts": [
            {
                "artifactId": f"art-{secrets.token_hex(4)}",
                "name": "result",
                "parts": [{"kind": "text", "text": json.dumps(result, ensure_ascii=False)}],
            }
        ],
        "metadata": {"correlation_id": correlation_id, "agent": result.get("agent", "")},
    }
    TASKS[task_id] = task
    return task


def create_agent_app(agent_id: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> FastAPI:
    card = a2a_core.agent_card(agent_id)
    app = FastAPI(
        title=card["name"],
        description=card["description"],
        version=card["version"],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/.well-known/agent.json")
    @app.get("/.well-known/agent-card.json")
    async def get_card() -> JSONResponse:
        return JSONResponse(card)

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "agent": agent_id,
                "name": card["name"],
                "protocol": "A2A 0.3.0 / JSON-RPC 2.0",
                "timestamp": _now(),
            }
        )

    @app.get("/")
    async def root() -> JSONResponse:
        return JSONResponse(
            {
                "agent": card["name"],
                "protocol": "A2A 0.3.0",
                "card": "/.well-known/agent.json",
                "rpc": "POST / (message/send)",
                "rest": "POST /run",
            }
        )

    @app.post("/run")
    async def run(request: Request) -> JSONResponse:
        payload = await request.json()
        started = time.perf_counter()
        result = handler(payload)
        return JSONResponse(
            {
                "ok": True,
                "agent": agent_id,
                "result": result,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )

    @app.post("/")
    async def rpc(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )
        rpc_id = body.get("id")
        method = body.get("method", "")
        params = body.get("params", {}) or {}
        if method == "tasks/get":
            task_id = params.get("id") or params.get("taskId")
            task = TASKS.get(task_id)
            if not task:
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {"code": -32001, "message": f"Tâche inconnue : {task_id}"},
                    },
                    status_code=404,
                )
            return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": task})
        if method != "message/send":
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Méthode non supportée : {method}"},
                },
                status_code=400,
            )
        message = params.get("message", {})
        metadata = params.get("metadata", {}) or {}
        question = _extract_text(message)
        payload = {**metadata, "question": question or metadata.get("question", "")}
        context_id = message.get("contextId") or metadata.get("correlation_id") or f"ctx-{secrets.token_hex(4)}"
        started = time.perf_counter()
        try:
            result = handler(payload)
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32000, "message": str(exc)},
                },
                status_code=500,
            )
        task = _task_from_result(
            f"task-{secrets.token_hex(4)}", context_id, result, metadata.get("correlation_id", context_id)
        )
        task["metadata"].update(
            {
                "agent_id": agent_id,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": {"task": task}})

    return app
