# -*- coding: utf-8 -*-
"""Lance l'écosystème de démonstration EduAgentic.

    python a2a/run_all.py                  # MCP + 3 agents + orchestrateur
    python a2a/run_all.py --with-dashboard # + dashboard Streamlit sur 8011

Les processus sont indépendants : chaque agent possède son port et sa propre
AgentCard, ce qui permet de démontrer la découverte A2A.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "a2a" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def start(name: str, args: list[str], cwd: Path = ROOT) -> subprocess.Popen:
    log_path = LOG_DIR / f"{name}.log"
    log = log_path.open("a", encoding="utf-8")
    print(f"  → {name:20s} {log_path.name}")
    return subprocess.Popen(
        [sys.executable, *args],
        cwd=str(cwd),
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Lance la démo MCP + A2A EduAgentic")
    parser.add_argument("--with-mcp", action="store_true", default=True)
    parser.add_argument("--with-dashboard", action="store_true")
    parser.add_argument("--no-mcp", dest="with_mcp", action="store_false")
    args = parser.parse_args()
    processes: list[tuple[str, subprocess.Popen]] = []
    print("=" * 74)
    print("EduAgentic · démarrage de l'écosystème")
    print("=" * 74)
    if args.with_mcp:
        processes.append(("mcp-8000", start("mcp", ["mcp_server/edumcp_server.py"])))
    for agent, port in (("agent-tuteur", 8101), ("agent-evaluation", 8102), ("agent-orientation", 8103)):
        processes.append(
            (agent, start(agent, ["a2a/agents.py", "--agent", agent, "--port", str(port)]))
        )
    processes.append(("orchestrateur", start("orchestrateur", ["a2a/orchestrator.py", "--port", "8001"])))
    if args.with_dashboard:
        processes.append(
            (
                "dashboard",
                start(
                    "dashboard",
                    ["-m", "streamlit", "run", "dashboard/app.py", "--server.port", "8011", "--server.headless", "true"],
                ),
            )
        )
    time.sleep(2.5)
    print("-" * 74)
    print("MCP SSE        : http://127.0.0.1:8000/sse")
    print("MCP health     : http://127.0.0.1:8000/api/health")
    print("A2A orchestr.  : http://127.0.0.1:8001")
    print("AgentCards     : http://127.0.0.1:8101/.well-known/agent.json")
    print("Dashboard      : http://localhost:8011")
    print("Logs           :", LOG_DIR)
    print("Ctrl+C pour arrêter tous les processus.")
    print("=" * 74)
    try:
        while all(proc.poll() is None for _, proc in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt…")
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                proc.terminate()
        for name, proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("Tous les processus sont arrêtés.")


if __name__ == "__main__":
    main()
