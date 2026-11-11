# -*- coding: utf-8 -*-
"""Logique A2A EduAgentic : AgentCards, découverte, délégation, orchestration.

Le protocole exposé par chaque agent est JSON-RPC 2.0 (message/send, tasks/get)
et les cartes sont publiées sur /.well-known/agent.json. L'orchestrateur peut
appeler les agents par HTTP ; en l'absence de serveur, il bascule sur le même
handler en local pour que la démonstration reste reproductible.
"""
from __future__ import annotations

import json
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

from shared import edtech_core as core

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CARDS_DIR = ROOT / "a2a" / "agent_cards"
LIVE_LOG = DATA / "a2a_live.jsonl"

AGENT_PORTS = {
    "agent-tuteur": 8101,
    "agent-evaluation": 8102,
    "agent-orientation": 8103,
    "orchestrateur": 8001,
}

AGENT_LABELS = {
    "agent-tuteur": "Agent Tuteur",
    "agent-evaluation": "Agent Évaluation",
    "agent-orientation": "Agent Orientation",
    "orchestrateur": "Orchestrateur A2A",
}

AGENT_COLORS = {
    "agent-tuteur": "#16A6A1",
    "agent-evaluation": "#F4B400",
    "agent-orientation": "#3B82C4",
    "orchestrateur": "#0B2340",
}


def agent_card(agent_id: str) -> dict[str, Any]:
    """Construit une AgentCard conforme au modèle A2A (version 0.3.0)."""
    port = AGENT_PORTS.get(agent_id, 8001)
    common = {
        "protocolVersion": "0.3.0",
        "preferredTransport": "JSONRPC",
        "additionalInterfaces": [{"url": f"http://127.0.0.1:{port}/", "transport": "JSONRPC"}],
        "provider": {
            "organization": "EduAgentic · Centre des Très Petites Entreprises Solidaires / DBA Technology",
            "url": "http://localhost:8011",
        },
        "version": "1.0.0",
        "documentationUrl": "http://localhost:8011",
        "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": True},
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "url": f"http://127.0.0.1:{port}/",
        "iconUrl": "http://localhost:8011/assets/logo.png",
    }
    if agent_id == "agent-tuteur":
        common.update(
            {
                "name": "Agent Tuteur",
                "description": "Recherche des ressources, vérifie les prérequis et recommande un parcours personnalisé.",
                "skills": [
                    {
                        "id": "search_courses",
                        "name": "Recherche de cours",
                        "description": "Trouve les cours et ressources adaptés à un objectif, un niveau ou une compétence.",
                        "tags": ["cours", "ressources", "catalogue", "recherche"],
                        "examples": ["Quels cours pour apprendre pandas ?", "Ressources niveau intermédiaire en SQL"],
                        "inputModes": ["text/plain", "application/json"],
                        "outputModes": ["application/json"],
                    },
                    {
                        "id": "recommend_learning_path",
                        "name": "Parcours personnalisé",
                        "description": "Ordonne les cours et prérequis jusqu'à la compétence visée.",
                        "tags": ["parcours", "prérequis", "tutorat", "compétences"],
                        "examples": ["Construis mon parcours Data Analyst"],
                        "inputModes": ["application/json"],
                        "outputModes": ["application/json"],
                    },
                ],
            }
        )
    elif agent_id == "agent-evaluation":
        common.update(
            {
                "name": "Agent Évaluation",
                "description": "Génère des quiz formatifs, corrige les réponses et produit un feedback de remédiation.",
                "skills": [
                    {
                        "id": "generate_quiz",
                        "name": "Génération de quiz",
                        "description": "Crée un quiz à partir de la banque de questions du cours.",
                        "tags": ["quiz", "évaluation", "formative"],
                        "examples": ["Génère 3 questions sur Python"],
                        "inputModes": ["application/json"],
                        "outputModes": ["application/json"],
                    },
                    {
                        "id": "grade_quiz",
                        "name": "Correction et feedback",
                        "description": "Calcule le score, montre les corrections et propose une remédiation.",
                        "tags": ["score", "feedback", "remédiation"],
                        "examples": ["Corrige mes réponses au quiz PY101"],
                        "inputModes": ["application/json"],
                        "outputModes": ["application/json"],
                    },
                ],
            }
        )
    elif agent_id == "agent-orientation":
        common.update(
            {
                "name": "Agent Orientation",
                "description": "Analyse l'écart de compétences et propose une trajectoire métier réaliste.",
                "skills": [
                    {
                        "id": "skill_gap",
                        "name": "Analyse de l'écart de compétences",
                        "description": "Compare les compétences acquises aux compétences attendues pour l'objectif.",
                        "tags": ["compétences", "gap", "diagnostic"],
                        "examples": ["Quelles compétences me manquent pour être Data Analyst ?"],
                        "inputModes": ["application/json"],
                        "outputModes": ["application/json"],
                    },
                    {
                        "id": "career_path",
                        "name": "Trajectoire métier",
                        "description": "Décrit les missions, le marché et les prochaines étapes du métier visé.",
                        "tags": ["orientation", "métier", "carrière", "parcours"],
                        "examples": ["Comment devenir Data Scientist ?"],
                        "inputModes": ["text/plain", "application/json"],
                        "outputModes": ["application/json"],
                    },
                ],
            }
        )
    else:
        common.update(
            {
                "name": "Orchestrateur A2A",
                "description": "Découvre les agents disponibles, sélectionne les spécialistes et délègue les tâches avec un correlation_id.",
                "skills": [
                    {
                        "id": "orchestrate_learning_request",
                        "name": "Orchestration de demande d'apprentissage",
                        "description": "Décompose une demande, découvre les AgentCards et consolide les réponses.",
                        "tags": ["orchestration", "délégation", "découverte", "A2A"],
                        "examples": ["Je veux devenir Data Analyst : parcours, cours et quiz"],
                        "inputModes": ["text/plain", "application/json"],
                        "outputModes": ["application/json"],
                    }
                ],
            }
        )
    return common


def save_agent_cards() -> list[Path]:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for agent_id in AGENT_PORTS:
        path = CARDS_DIR / f"{agent_id}.json"
        path.write_text(json.dumps(agent_card(agent_id), ensure_ascii=False, indent=2), encoding="utf-8")
        paths.append(path)
    return paths


def discover_agents(timeout: float = 1.5, use_network: bool = True) -> list[dict[str, Any]]:
    """Découverte A2A : lit les AgentCards locales et tente le endpoint HTTP de chaque agent."""
    cards = []
    for agent_id in ("agent-tuteur", "agent-evaluation", "agent-orientation"):
        local = agent_card(agent_id)
        status = "déclarée"
        latency = 0
        if use_network:
            started = time.perf_counter()
            try:
                response = requests.get(
                    f"http://127.0.0.1:{AGENT_PORTS[agent_id]}/.well-known/agent.json", timeout=timeout
                )
                if response.ok:
                    local = response.json()
                    status = "en ligne"
            except requests.RequestException:
                status = "hors ligne (carte locale)"
            latency = round((time.perf_counter() - started) * 1000, 1)
        cards.append(
            {
                "agent_id": agent_id,
                "label": AGENT_LABELS[agent_id],
                "status": status,
                "latency_ms": latency,
                "card": local,
            }
        )
    return cards


def _text_from_payload(payload: dict[str, Any]) -> str:
    return " ".join(
        str(payload.get(key, ""))
        for key in ("question", "objective", "message", "target_skill")
        if payload.get(key)
    ).strip()


def handle_tuteur(payload: dict[str, Any]) -> dict[str, Any]:
    learner_id = payload.get("learner_id") or "L001"
    target = payload.get("target_skill") or ""
    query = target or payload.get("objective") or payload.get("question") or "cours"
    profile = core.get_learner_profile(learner_id)
    path = core.recommend_learning_path(learner_id, target or profile["target_skill"])
    courses = core.search_courses(query=query, level=payload.get("level") or None, max_results=4)
    return {
        "agent": "agent-tuteur",
        "learner": profile,
        "path": path,
        "courses": courses["results"],
        "summary": (
            f"J'ai identifié {len(path['path'])} étape(s) pour {profile['name']} "
            f"et {len(courses['results'])} ressource(s) pertinente(s)."
        ),
    }


def handle_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    learner_id = payload.get("learner_id") or "L001"
    course_id = payload.get("course_id")
    if not course_id:
        profile = core.get_learner_profile(learner_id)
        next_course = profile.get("recommended_next") or {}
        course_id = next_course.get("id") or "PY101"
    if payload.get("answers"):
        result = core.grade_quiz(learner_id, course_id, payload["answers"])
        return {
            "agent": "agent-evaluation",
            "mode": "correction",
            "course_id": course_id,
            "result": result,
            "summary": f"Score : {result['score']}/100 — {result['feedback']}",
        }
    quiz = core.generate_quiz(course_id, payload.get("difficulty"), payload.get("n_questions", 3))
    return {
        "agent": "agent-evaluation",
        "mode": "generation",
        "course_id": course_id,
        "quiz": quiz,
        "summary": f"Quiz {quiz['quiz_id']} généré : {quiz['question_count']} questions sur « {quiz['course_title']} ».",
    }


def handle_orientation(payload: dict[str, Any]) -> dict[str, Any]:
    learner_id = payload.get("learner_id") or "L001"
    profile = core.get_learner_profile(learner_id)
    target = payload.get("target_skill") or profile["target_skill"]
    path = core.recommend_learning_path(learner_id, target)
    courses_data = core.courses()
    by_id = {c["id"]: c for c in courses_data}
    completed_ids = [c["id"] for c in profile["completed_courses"]]
    acquired = sorted(
        {
            skill
            for cid in completed_ids
            for skill in by_id.get(cid, {}).get("skills", [])
        }
    )
    required = sorted({skill for step in path["path"] for skill in by_id.get(step["id"], {}).get("skills", [])})
    missing = [s for s in required if s not in acquired]
    return {
        "agent": "agent-orientation",
        "learner": profile,
        "target_skill": target,
        "target_label": core.skill_label(target),
        "acquired_skills": [core.skill_label(s) for s in acquired],
        "missing_skills": [core.skill_label(s) for s in missing],
        "path": path,
        "summary": (
            f"Pour viser « {core.skill_label(target)} », il reste {len(missing)} compétence(s) à renforcer "
            f"et {path['total_hours']} h de formation."
        ),
    }


LOCAL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "agent-tuteur": handle_tuteur,
    "agent-evaluation": handle_evaluation,
    "agent-orientation": handle_orientation,
}


def call_agent(
    agent_id: str,
    payload: dict[str, Any],
    correlation_id: str,
    timeout: float = 6.0,
    use_network: bool = True,
) -> dict[str, Any]:
    """Appelle un agent en JSON-RPC ; repli local si le serveur n'est pas joignable."""
    started = time.perf_counter()
    url = f"http://127.0.0.1:{AGENT_PORTS[agent_id]}/"
    task_text = _text_from_payload(payload) or "Demande d'apprentissage"
    rpc = {
        "jsonrpc": "2.0",
        "id": f"req-{secrets.token_hex(4)}",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": task_text}],
                "messageId": f"msg-{secrets.token_hex(4)}",
                "contextId": correlation_id,
            },
            "metadata": {"correlation_id": correlation_id, **payload},
        },
    }
    used = "http"
    try:
        if not use_network:
            raise ConnectionError("réseau désactivé pour la démonstration locale")
        response = requests.post(url, json=rpc, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        if "error" in body:
            raise RuntimeError(body["error"].get("message", "erreur JSON-RPC"))
        task = body.get("result", {}).get("task", {})
        artifact = (task.get("artifacts") or [{}])[0]
        text = (artifact.get("parts") or [{}])[0].get("text", "{}")
        result = json.loads(text)
        status = "completed"
    except Exception:  # noqa: BLE001 - bascule locale volontaire
        used = "local"
        result = LOCAL_HANDLERS[agent_id](payload)
        status = "completed (repli local)"
    latency = round((time.perf_counter() - started) * 1000, 1)
    delegation = {
        "correlation_id": correlation_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "orchestrateur",
        "target": agent_id,
        "skill": (result.get("summary") and agent_id) or agent_id,
        "task": task_text[:160],
        "status": "completed" if status.startswith("completed") else status,
        "latency_ms": latency,
        "transport": used,
    }
    return {
        "agent_id": agent_id,
        "label": AGENT_LABELS[agent_id],
        "status": status,
        "transport": used,
        "latency_ms": latency,
        "payload": payload,
        "result": result,
        "delegation": delegation,
    }


def _build_answer(learner: dict[str, Any], orientation: dict[str, Any], tuteur: dict[str, Any], evaluation: dict[str, Any]) -> str:
    path = orientation.get("path", {}).get("path", [])
    path_lines = "\n".join(
        f"{i}. **{step['id']} — {step['title']}** ({step['duration_h']} h, {step['level']})"
        for i, step in enumerate(path, 1)
    ) or "Aucun cours restant : le parcours est déjà validé."
    course_lines = "\n".join(
        f"- **{c['id']} · {c['title']}** — {c['level']}, {c['duration_h']} h, pertinence {int(c['relevance']*100)} %"
        for c in tuteur.get("courses", [])[:4]
    ) or "- Aucune ressource supplémentaire."
    quiz = evaluation.get("quiz", {})
    quiz_line = (
        f"Quiz **{quiz.get('quiz_id')}** ({quiz.get('question_count')} questions sur {quiz.get('course_title')})"
        if quiz
        else evaluation.get("summary", "Évaluation disponible à la demande.")
    )
    return (
        f"### Synthèse pour {learner['name']}\n\n"
        f"**Objectif** : {learner['goal']} · **niveau** : {learner['level']} · "
        f"**progression** : {learner['progress_pct']} %.\n\n"
        f"**1. Parcours recommandé ({orientation.get('path', {}).get('total_hours', 0)} h)**\n{path_lines}\n\n"
        f"**2. Compétences à renforcer** : {', '.join(orientation.get('missing_skills', [])) or 'aucune'}.\n\n"
        f"**3. Ressources du catalogue**\n{course_lines}\n\n"
        f"**4. Évaluation formative** : {quiz_line}.\n\n"
        f"> Chaque délégation est tracée par un `correlation_id` et un log horodaté : "
        f"la réponse est vérifiable de bout en bout."
    )


def orchestrate_request(
    learner_id: str = "L001",
    objective: str = "",
    question: str = "",
    target_skill: str = "",
    course_id: str = "",
    use_network: bool = True,
) -> dict[str, Any]:
    """Découvre les agents, délègue en parallèle et agrège une réponse unique."""
    started = time.perf_counter()
    correlation_id = f"A2A-{datetime.now().strftime('%y%m%d-%H%M%S')}-{secrets.token_hex(2).upper()}"
    profile = core.get_learner_profile(learner_id)
    target = target_skill or profile["target_skill"]
    goal = objective or profile["goal"]
    question = question or f"Comment atteindre mon objectif : {goal} ?"
    cards = discover_agents(use_network=use_network)
    base_payload = {
        "learner_id": profile["id"],
        "objective": goal,
        "question": question,
        "target_skill": target,
    }
    jobs = {
        "agent-orientation": dict(base_payload),
        "agent-tuteur": dict(base_payload),
        "agent-evaluation": {**base_payload, "course_id": course_id or "", "n_questions": 3},
    }
    delegations: list[dict[str, Any]] = []
    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(call_agent, agent_id, payload, correlation_id, 6.0, use_network): agent_id
            for agent_id, payload in jobs.items()
        }
        for future in as_completed(futures):
            agent_id = futures[future]
            try:
                delegation = future.result()
            except Exception as exc:  # noqa: BLE001
                delegation = {
                    "agent_id": agent_id,
                    "label": AGENT_LABELS[agent_id],
                    "status": "failed",
                    "transport": "local",
                    "latency_ms": 0,
                    "payload": jobs[agent_id],
                    "result": {"summary": str(exc)},
                    "delegation": {
                        "correlation_id": correlation_id,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "orchestrateur",
                        "target": agent_id,
                        "task": question[:160],
                        "status": "failed",
                        "latency_ms": 0,
                        "transport": "local",
                    },
                }
            delegations.append(delegation)
            results[agent_id] = delegation["result"]
    # ordre stable pour l'affichage
    delegations.sort(key=lambda d: ["agent-orientation", "agent-tuteur", "agent-evaluation"].index(d["agent_id"]))
    orientation = results.get("agent-orientation", {})
    tuteur = results.get("agent-tuteur", {})
    evaluation = results.get("agent-evaluation", {})
    answer = _build_answer(profile, orientation, tuteur, evaluation)
    total_latency = round((time.perf_counter() - started) * 1000, 1)
    log_rows = []
    for delegation in delegations:
        row = dict(delegation["delegation"])
        row["correlation_id"] = correlation_id
        log_rows.append(row)
    LIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with LIVE_LOG.open("a", encoding="utf-8") as fh:
        for row in log_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {
        "correlation_id": correlation_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "learner": profile,
        "objective": goal,
        "question": question,
        "agents_discovered": cards,
        "delegations": delegations,
        "answer": answer,
        "artifacts": {
            "orientation": orientation,
            "tuteur": tuteur,
            "evaluation": evaluation,
        },
        "total_latency_ms": total_latency,
        "protocol": {
            "version": "A2A 0.3.0",
            "discovery": "/.well-known/agent.json",
            "rpc": "message/send",
            "trace": "correlation_id",
        },
    }


def recent_traces(limit: int = 8) -> list[dict[str, Any]]:
    if not LIVE_LOG.exists():
        return []
    rows = []
    for line in LIVE_LOG.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
