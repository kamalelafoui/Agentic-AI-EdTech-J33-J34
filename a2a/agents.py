# -*- coding: utf-8 -*-
"""Trois agents spécialisés A2A : Tuteur, Évaluation et Orientation."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from a2a.protocol import create_agent_app  # noqa: E402
from shared import a2a_core  # noqa: E402

HANDLERS = {
    "agent-tuteur": a2a_core.handle_tuteur,
    "agent-evaluation": a2a_core.handle_evaluation,
    "agent-orientation": a2a_core.handle_orientation,
}


def build(agent_id: str):
    return create_agent_app(agent_id, HANDLERS[agent_id])


app_tuteur = build("agent-tuteur")
app_evaluation = build("agent-evaluation")
app_orientation = build("agent-orientation")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent A2A EduAgentic")
    parser.add_argument("--agent", choices=list(HANDLERS), required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    port = args.port or a2a_core.AGENT_PORTS[args.agent]
    app = build(args.agent)
    uvicorn.run(app, host=args.host, port=port, log_level="info")


if __name__ == "__main__":
    main()
