# -*- coding: utf-8 -*-
"""Serveur MCP EduAgentic — expose les outils EdTech à un agent Langflow.

Transport principal : SSE (compatible Langflow MCP Tools et ngrok).
Pont REST local : /api/health, /api/tools, /api/tool (utilisé par le dashboard).

Lancement :
    python mcp_server/edumcp_server.py
    python mcp_server/edumcp_server.py --transport streamable-http --port 8000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402

from shared import edtech_core as core  # noqa: E402

SERVER_NAME = "edumcp-edtech"
STARTED_AT = time.time()

mcp = FastMCP(
    SERVER_NAME,
    instructions=(
        "Serveur MCP EduAgentic pour une plateforme d'apprentissage. "
        "Utilisez les outils pour rechercher des cours, consulter un profil, "
        "construire un parcours, générer/corriger un quiz et obtenir les statistiques. "
        "Toutes les données sont synthétiques et les réponses doivent rester en français."
    ),
    host="127.0.0.1",
    port=8000,
    sse_path="/sse",
    message_path="/messages/",
    streamable_http_path="/mcp",
    log_level="INFO",
)


@mcp.tool()
def search_courses(query: str = "", level: str = "", max_results: int = 5) -> dict[str, Any]:
    """Recherche des cours EdTech par mots-clés (titre, compétence, tag) et filtre par niveau.

    Args:
        query: Mots-clés en langage naturel, par exemple « data analyst python ».
        level: Débutant, Intermédiaire, Avancé, ou vide pour tous les niveaux.
        max_results: Nombre maximum de cours retournés (1 à 10).
    """
    return core.search_courses(query=query, level=level or None, max_results=max_results)


@mcp.tool()
def get_learner_profile(learner_id: str) -> dict[str, Any]:
    """Retourne le profil d'un apprenant : niveau, objectif, progression, cours validés et prochain cours.

    Args:
        learner_id: Identifiant L001 à L024, ou nom exact de l'apprenant.
    """
    return core.get_learner_profile(learner_id)


@mcp.tool()
def recommend_learning_path(learner_id: str, target_skill: str = "") -> dict[str, Any]:
    """Construit un parcours d'apprentissage ordonné, prérequis inclus, vers une compétence cible.

    Args:
        learner_id: Identifiant ou nom de l'apprenant.
        target_skill: Compétence visée (data-analysis, machine-learning, nlp, etc.). Vide = objectif du profil.
    """
    return core.recommend_learning_path(learner_id, target_skill or None)


@mcp.tool()
def generate_quiz(course_id: str, difficulty: str = "", n_questions: int = 3) -> dict[str, Any]:
    """Génère un quiz formatif pour un cours, sans révéler les réponses.

    Args:
        course_id: Identifiant du cours (ex. PY101, SQL201, STAT210, VIZ220, ML301, GEN130).
        difficulty: facile, moyen, difficile, ou vide pour toutes les difficultés.
        n_questions: Nombre de questions (1 à 5).
    """
    return core.generate_quiz(course_id, difficulty or None, n_questions)


@mcp.tool()
def grade_quiz(learner_id: str, course_id: str, answers: dict[str, int]) -> dict[str, Any]:
    """Corrige un quiz et renvoie le score, les corrections et un feedback de remédiation.

    Args:
        learner_id: Identifiant ou nom de l'apprenant.
        course_id: Identifiant du cours.
        answers: Dictionnaire {question_id: index_de_la_réponse}, index de 0 à 3.
    """
    return core.grade_quiz(learner_id, course_id, answers)


@mcp.tool()
def get_learning_statistics(segment: str = "Tous") -> dict[str, Any]:
    """Agrège les KPI et séries du dashboard : scores, cohortes, complétion, délégations A2A.

    Args:
        segment: Nom exact d'une cohorte, ou « Tous » pour l'ensemble.
    """
    return core.learning_statistics(segment)


def _dispatch(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    handlers = {
        "search_courses": lambda: core.search_courses(
            query=args.get("query", ""),
            level=args.get("level") or None,
            max_results=args.get("max_results", 5),
        ),
        "get_learner_profile": lambda: core.get_learner_profile(args.get("learner_id", "")),
        "recommend_learning_path": lambda: core.recommend_learning_path(
            args.get("learner_id", ""), args.get("target_skill") or None
        ),
        "generate_quiz": lambda: core.generate_quiz(
            args.get("course_id", ""), args.get("difficulty") or None, args.get("n_questions", 3)
        ),
        "grade_quiz": lambda: core.grade_quiz(
            args.get("learner_id", ""), args.get("course_id", ""), args.get("answers", {})
        ),
        "get_learning_statistics": lambda: core.learning_statistics(args.get("segment", "Tous")),
    }
    if tool_name not in handlers:
        raise ValueError(f"Outil inconnu : {tool_name}")
    return handlers[tool_name]()


@mcp.custom_route("/api/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "server": SERVER_NAME,
            "transport": "SSE",
            "sse_url": "http://127.0.0.1:8000/sse",
            "uptime_s": round(time.time() - STARTED_AT, 1),
            "tools": [t["name"] for t in core.list_tools()],
            "storage": core.storage_status(),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )


@mcp.custom_route("/api/tools", methods=["GET"])
async def tools_list(request: Request) -> JSONResponse:
    return JSONResponse({"count": len(core.list_tools()), "tools": core.list_tools()})


@mcp.custom_route("/api/tool", methods=["POST"])
async def tool_call(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
        tool_name = payload.get("tool", "")
        args = payload.get("arguments", {}) or {}
        started = time.perf_counter()
        result = _dispatch(tool_name, args)
        return JSONResponse(
            {
                "ok": True,
                "tool": tool_name,
                "arguments": args,
                "result": result,
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
    except Exception as exc:  # noqa: BLE001 - renvoyé au dashboard
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP EduAgentic")
    parser.add_argument("--transport", choices=["sse", "streamable-http", "stdio"], default="sse")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    banner = {
        "server": SERVER_NAME,
        "transport": args.transport,
        "host": args.host,
        "port": args.port,
        "sse": f"http://{args.host}:{args.port}/sse" if args.transport == "sse" else None,
        "streamable_http": f"http://{args.host}:{args.port}/mcp" if args.transport == "streamable-http" else None,
        "tools": [t["name"] for t in core.list_tools()],
    }
    print("=" * 72)
    print("EduMCP · serveur MCP EdTech")
    print(json.dumps(banner, ensure_ascii=False, indent=2))
    print("=" * 72, flush=True)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
