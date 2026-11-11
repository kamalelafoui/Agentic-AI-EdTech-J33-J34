# -*- coding: utf-8 -*-
"""Orchestrateur A2A : découverte des AgentCards, sélection et délégation.

Expose aussi un endpoint REST /orchestrate pour le dashboard Streamlit.
"""
from __future__ import annotations

import json
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import a2a_core  # noqa: E402

app = FastAPI(
    title="Orchestrateur A2A EduAgentic",
    description="Découverte, sélection et délégation vers les agents Tuteur, Évaluation et Orientation.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CARD = a2a_core.agent_card("orchestrateur")
TASKS: dict[str, dict[str, Any]] = {}


def _task(result: dict[str, Any], context_id: str) -> dict[str, Any]:
    task_id = f"task-{secrets.token_hex(4)}"
    task = {
        "kind": "task",
        "id": task_id,
        "contextId": context_id,
        "status": {"state": "completed", "timestamp": datetime.now().isoformat(timespec="seconds")},
        "artifacts": [
            {
                "artifactId": f"art-{secrets.token_hex(4)}",
                "name": "orchestration",
                "parts": [{"kind": "text", "text": json.dumps(result, ensure_ascii=False)}],
            }
        ],
        "metadata": {
            "correlation_id": result["correlation_id"],
            "agents": [d["agent_id"] for d in result["delegations"]],
            "total_latency_ms": result["total_latency_ms"],
        },
    }
    TASKS[task_id] = task
    return task


@app.get("/.well-known/agent.json")
@app.get("/.well-known/agent-card.json")
async def agent_card() -> JSONResponse:
    return JSONResponse(CARD)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "agent": CARD["name"],
            "protocol": "A2A 0.3.0",
            "card": "/.well-known/agent.json",
            "rpc": "POST / (message/send)",
            "rest": "POST /orchestrate",
            "discovery": "GET /discover",
        }
    )


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "agent": "orchestrateur",
            "protocol": "A2A 0.3.0 / JSON-RPC 2.0",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )


@app.get("/discover")
async def discover() -> JSONResponse:
    cards = a2a_core.discover_agents()
    return JSONResponse({"count": len(cards), "agents": cards})


@app.post("/orchestrate")
async def orchestrate(request: Request) -> JSONResponse:
    payload = await request.json()
    started = time.perf_counter()
    result = a2a_core.orchestrate_request(
        learner_id=payload.get("learner_id", "L001"),
        objective=payload.get("objective", ""),
        question=payload.get("question", ""),
        target_skill=payload.get("target_skill", ""),
        course_id=payload.get("course_id", ""),
        use_network=payload.get("use_network", True),
    )
    return JSONResponse(
        {
            "ok": True,
            "result": result,
            "api_latency_ms": round((time.perf_counter() - started) * 1000, 1),
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
        task = TASKS.get(params.get("id") or params.get("taskId"))
        if not task:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32001, "message": "Tâche inconnue"},
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
    text = "\n".join(
        part.get("text", "")
        for part in message.get("parts", [])
        if isinstance(part, dict) and part.get("kind") == "text"
    ).strip()
    result = a2a_core.orchestrate_request(
        learner_id=metadata.get("learner_id", "L001"),
        objective=metadata.get("objective", ""),
        question=text or metadata.get("question", ""),
        target_skill=metadata.get("target_skill", ""),
        course_id=metadata.get("course_id", ""),
        use_network=metadata.get("use_network", True),
    )
    task = _task(result, message.get("contextId") or result["correlation_id"])
    return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": {"task": task}})


def main() -> None:
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Orchestrateur A2A EduAgentic")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
