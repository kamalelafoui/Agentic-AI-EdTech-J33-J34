# -*- coding: utf-8 -*-
"""Moteur métier partagé EduAgentic.

Ce module est utilisé par :
- le serveur MCP (mcp_server/edumcp_server.py) ;
- le dashboard Streamlit (dashboard/app.py) ;
- les agents A2A (a2a/agents.py).

Il ne dépend que de la bibliothèque standard : les mêmes fonctions peuvent donc
tourner sans clé API ni service externe.
"""
from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from shared import mongo_store

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SKILL_LABELS = {
    "python": "Python",
    "sql": "SQL",
    "statistics": "Statistiques",
    "data-analysis": "Analyse de données",
    "visualization": "Visualisation",
    "machine-learning": "Machine Learning",
    "nlp": "NLP & IA générative",
    "deep-learning": "Deep Learning",
    "mlops": "MLOps",
    "cloud": "Cloud",
    "data-engineering": "Data Engineering",
    "ethics": "Éthique de l'IA",
    "governance": "Gouvernance",
    "ux": "UX/UI",
    "design": "Design",
    "pedagogy": "Pédagogie",
    "instructional-design": "Ingénierie pédagogique",
    "prompting": "Prompt engineering",
    "portfolio": "Portfolio",
}

DOMAINS = {
    "data-analysis": "Data & BI",
    "sql": "Data & BI",
    "statistics": "Data & BI",
    "visualization": "Data & BI",
    "portfolio": "Data & BI",
    "machine-learning": "IA & ML",
    "nlp": "IA & ML",
    "deep-learning": "IA & ML",
    "mlops": "IA & ML",
    "prompting": "IA & ML",
    "cloud": "Cloud & Engineering",
    "data-engineering": "Cloud & Engineering",
    "ethics": "Pédagogie & Éthique",
    "governance": "Pédagogie & Éthique",
    "pedagogy": "Pédagogie & Éthique",
    "instructional-design": "Pédagogie & Éthique",
    "ux": "Design",
    "design": "Design",
}

LEVEL_ORDER = {"Débutant": 0, "Intermédiaire": 1, "Avancé": 2}


def _read_json(name: str) -> Any:
    with (DATA / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def courses() -> list[dict[str, Any]]:
    if mongo_store.enabled():
        docs = mongo_store.read("courses")
        if docs:
            return docs
    return _read_json("courses.json")


def learners() -> list[dict[str, Any]]:
    if mongo_store.enabled():
        docs = mongo_store.read("learners")
        if docs:
            return docs
    return _read_json("learners.json")


def quiz_bank() -> list[dict[str, Any]]:
    if mongo_store.enabled():
        docs = mongo_store.read("quiz_bank")
        if docs:
            return docs
    return _read_json("quiz_bank.json")


def attempts() -> list[dict[str, str]]:
    if mongo_store.enabled():
        docs = mongo_store.read("quiz_attempts")
        if docs:
            return docs
    return _read_csv("quiz_attempts.csv")


def delegations() -> list[dict[str, str]]:
    if mongo_store.enabled():
        docs = mongo_store.read("a2a_delegations")
        if docs:
            return docs
    return _read_csv("a2a_delegations.csv")


def site_meta() -> dict[str, Any]:
    return _read_json("site.json")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def skill_label(skill: str) -> str:
    return SKILL_LABELS.get(skill, skill.replace("-", " ").title())


def domain_for(skill: str) -> str:
    return DOMAINS.get(skill, "Autres")


def _course_by_id(course_id: str) -> dict[str, Any]:
    target = normalize(course_id)
    for course in courses():
        if normalize(course["id"]) == target:
            return course
    # tolérance : identifiant partiel ou titre
    matches = [c for c in courses() if target in normalize(c["id"]) or target in normalize(c["title"])]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"Cours introuvable : {course_id}. Identifiants disponibles : {', '.join(c['id'] for c in courses())}.")


def _learner_by_id(identifier: str) -> dict[str, Any]:
    target = normalize(identifier)
    for learner in learners():
        if normalize(learner["id"]) == target:
            return learner
    matches = [l for l in learners() if target in normalize(l["name"]) or normalize(l["name"]) in target]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(
            f"Apprenant introuvable : {identifier}. Utilisez un identifiant L001 à L024 ou un nom exact."
        )
    names = ", ".join(l["name"] for l in matches[:5])
    raise ValueError(f"Plusieurs apprenants correspondent à « {identifier} » : {names}.")


def search_courses(query: str = "", level: str | None = None, max_results: int = 5) -> dict[str, Any]:
    """Recherche des cours du catalogue EdTech par mots-clés, compétence ou niveau."""
    q = normalize(query or "").strip()
    tokens = [t for t in q.replace(",", " ").split() if len(t) > 1]
    level_norm = normalize(level) if level and normalize(level) not in ("tous", "toutes", "any") else None
    scored: list[tuple[float, dict[str, Any]]] = []
    for course in courses():
        if level_norm and normalize(course["level"]) != level_norm:
            continue
        haystack = normalize(
            " ".join(
                [
                    course["id"],
                    course["title"],
                    course["description"],
                    course["provider"],
                    course["level"],
                    " ".join(course["skills"]),
                    " ".join(course["tags"]),
                ]
            )
        )
        score = 0.0
        if not tokens:
            score = float(course["rating"])
        for token in tokens:
            if token in normalize(course["title"]):
                score += 6
            if token in normalize(" ".join(course["tags"])):
                score += 4
            if token in normalize(" ".join(course["skills"])):
                score += 3
            if token in normalize(course["description"]):
                score += 1
        if tokens and score == 0:
            continue
        scored.append((score + course["rating"] / 10, course))
    scored.sort(key=lambda pair: (-pair[0], -pair[1]["rating"]))
    limit = max(1, min(int(max_results or 5), 10))
    max_score = scored[0][0] if scored else 1.0
    results = []
    for score, course in scored[:limit]:
        results.append(
            {
                "id": course["id"],
                "title": course["title"],
                "level": course["level"],
                "duration_h": course["duration_h"],
                "skills": [skill_label(s) for s in course["skills"]],
                "prerequisites": course["prerequisites"],
                "rating": course["rating"],
                "provider": course["provider"],
                "relevance": round(min(score / max_score, 1.0), 2),
            }
        )
    return {
        "query": query,
        "level": level or "Tous",
        "count": len(results),
        "results": results,
        "message": f"{len(results)} cours trouvé(s) pour « {query or 'catalogue'} ».",
    }


def get_learner_profile(learner_id: str) -> dict[str, Any]:
    """Retourne le profil, la progression et les compétences d'un apprenant."""
    learner = _learner_by_id(learner_id)
    by_id = {c["id"]: c for c in courses()}
    completed = [
        {
            "id": cid,
            "title": by_id[cid]["title"] if cid in by_id else cid,
            "skills": [skill_label(s) for s in by_id[cid]["skills"]] if cid in by_id else [],
        }
        for cid in learner["completed_courses"]
    ]
    attempts_for_learner = [a for a in attempts() if a["learner_id"] == learner["id"]]
    avg_attempt = (
        round(sum(int(a["score"]) for a in attempts_for_learner) / len(attempts_for_learner), 1)
        if attempts_for_learner
        else learner["quiz_average"]
    )
    return {
        "id": learner["id"],
        "name": learner["name"],
        "level": learner["level"],
        "cohort": learner["cohort"],
        "goal": learner["goal"],
        "target_skill": learner["target_skill"],
        "target_skill_label": skill_label(learner["target_skill"]),
        "progress_pct": learner["progress_pct"],
        "engagement": learner["engagement"],
        "quiz_average": avg_attempt,
        "completed_courses": completed,
        "attempts_count": len(attempts_for_learner),
        "status": learner["status"],
        "recommended_next": _next_course_for(learner),
    }


def _next_course_for(learner: dict[str, Any]) -> dict[str, Any] | None:
    target = learner["target_skill"]
    completed = set(learner["completed_courses"])
    candidates = [
        c
        for c in courses()
        if target in c["skills"] and c["id"] not in completed and set(c["prerequisites"]).issubset(completed)
    ]
    if not candidates:
        candidates = [c for c in courses() if target in c["skills"] and c["id"] not in completed]
    if not candidates:
        return None
    best = sorted(candidates, key=lambda c: (LEVEL_ORDER.get(c["level"], 9), -c["rating"]))[0]
    return {"id": best["id"], "title": best["title"], "level": best["level"], "duration_h": best["duration_h"]}


def _collect_prerequisites(course: dict[str, Any], by_id: dict[str, dict[str, Any]], seen: set[str]) -> None:
    for prereq in course["prerequisites"]:
        if prereq in seen:
            continue
        seen.add(prereq)
        if prereq in by_id:
            _collect_prerequisites(by_id[prereq], by_id, seen)


def recommend_learning_path(learner_id: str, target_skill: str | None = None) -> dict[str, Any]:
    """Construit un parcours ordonné (prérequis inclus) vers une compétence cible."""
    learner = _learner_by_id(learner_id)
    target_raw = target_skill or learner["target_skill"]
    target = normalize(target_raw).replace(" ", "-")
    # accepte les libellés français
    alias = {
        "data": "data-analysis",
        "analyse-de-donnees": "data-analysis",
        "data-analyst": "data-analysis",
        "business-intelligence": "visualization",
        "bi": "visualization",
        "ia": "machine-learning",
        "intelligence-artificielle": "machine-learning",
        "ml": "machine-learning",
        "deep-learning": "deep-learning",
        "nlp": "nlp",
        "ethique": "ethics",
        "pedagogie": "pedagogy",
        "ux": "ux",
    }
    target = alias.get(target, target)
    target_courses = [c for c in courses() if target in c["skills"]]
    if not target_courses:
        # recherche floue
        target_courses = [
            c
            for c in courses()
            if target in normalize(c["title"]) or target in normalize(" ".join(c["tags"]))
        ]
    if not target_courses:
        return {
            "learner_id": learner["id"],
            "learner_name": learner["name"],
            "target_skill": target_raw,
            "target_skill_label": skill_label(target),
            "path": [],
            "total_hours": 0,
            "message": f"Aucun cours ne couvre la compétence « {target_raw} » dans le catalogue.",
        }
    by_id = {c["id"]: c for c in courses()}
    completed = set(learner["completed_courses"])
    needed_ids: set[str] = set()
    target_ids: set[str] = set()

    def target_score(course: dict[str, Any]) -> tuple[float, int, float]:
        title = normalize(course["title"] + " " + " ".join(course["tags"]))
        label = normalize(skill_label(target))
        exact = 5.0 if label in title or target.replace("-", " ") in title else 0.0
        return (exact + LEVEL_ORDER.get(course["level"], 9), course["duration_h"], course["rating"])

    # On vise le cours cible le plus avancé et le plus pertinent, puis tous ses prérequis.
    available_targets = [c for c in target_courses if c["id"] not in completed]
    chosen_target = sorted(available_targets or target_courses, key=target_score, reverse=True)[0]
    needed_ids.add(chosen_target["id"])
    target_ids.add(chosen_target["id"])
    _collect_prerequisites(chosen_target, by_id, needed_ids)
    # retire les cours déjà validés
    remaining = [by_id[cid] for cid in needed_ids if cid in by_id and cid not in completed]
    # tri topologique simple : niveau puis prérequis satisfaits
    ordered: list[dict[str, Any]] = []
    pending = remaining[:]
    placed: set[str] = set(completed)
    while pending:
        ready = [c for c in pending if set(c["prerequisites"]).issubset(placed)]
        if not ready:
            ready = [min(pending, key=lambda c: LEVEL_ORDER.get(c["level"], 9))]
        ready.sort(key=lambda c: (LEVEL_ORDER.get(c["level"], 9), c["duration_h"]))
        course = ready[0]
        ordered.append(course)
        placed.add(course["id"])
        pending.remove(course)
    path = []
    for index, course in enumerate(ordered, 1):
        path.append(
            {
                "step": index,
                "id": course["id"],
                "title": course["title"],
                "level": course["level"],
                "duration_h": course["duration_h"],
                "skills": [skill_label(s) for s in course["skills"]],
                "prerequisites": course["prerequisites"],
                "provider": course["provider"],
                "reason": "Cours cible" if course["id"] in target_ids else "Prérequis indispensable",
            }
        )
    total_hours = sum(c["duration_h"] for c in ordered)
    met = set(learner["completed_courses"])
    already = [
        {"id": cid, "title": by_id[cid]["title"]}
        for cid in sorted(needed_ids & met)
        if cid in by_id
    ]
    return {
        "learner_id": learner["id"],
        "learner_name": learner["name"],
        "level": learner["level"],
        "goal": learner["goal"],
        "target_skill": target,
        "target_skill_label": skill_label(target),
        "path": path,
        "total_hours": total_hours,
        "steps": len(path),
        "already_validated": already,
        "message": (
            f"Parcours de {len(path)} étape(s), {total_hours} h, pour viser « {skill_label(target)} »."
            if path
            else f"Les prérequis de « {skill_label(target)} » sont déjà validés : vous pouvez passer au projet capstone."
        ),
    }


def generate_quiz(course_id: str, difficulty: str | None = None, n_questions: int = 3) -> dict[str, Any]:
    """Génère un quiz formatif à partir de la banque de questions du cours."""
    course = _course_by_id(course_id)
    pool = [q for q in quiz_bank() if q["course_id"] == course["id"]]
    diff = normalize(difficulty or "").strip()
    if diff and diff not in ("tous", "toutes", "any"):
        filtered = [q for q in pool if normalize(q["difficulty"]) == diff]
        pool = filtered or pool
    n = max(1, min(int(n_questions or 3), len(pool)))
    selected = pool[:n]
    quiz_id = "QUIZ-" + hashlib.sha1(
        (course["id"] + "|" + ",".join(q["id"] for q in selected)).encode()
    ).hexdigest()[:8].upper()
    questions = []
    for q in selected:
        questions.append(
            {
                "id": q["id"],
                "question": q["question"],
                "choices": q["choices"],
                "difficulty": q["difficulty"],
            }
        )
    return {
        "quiz_id": quiz_id,
        "course_id": course["id"],
        "course_title": course["title"],
        "difficulty": difficulty or "Tous niveaux",
        "question_count": len(questions),
        "questions": questions,
        "instructions": "Répondez avec l'index de la bonne réponse (0 à 3). Les corrections sont fournies après validation.",
    }


def grade_quiz(learner_id: str, course_id: str, answers: Any) -> dict[str, Any]:
    """Corrige un quiz et renvoie le score, les corrections et un feedback personnalisé."""
    learner = _learner_by_id(learner_id)
    course = _course_by_id(course_id)
    pool = [q for q in quiz_bank() if q["course_id"] == course["id"]]
    by_question = {q["id"]: q for q in pool}
    details = []
    correct = 0
    if isinstance(answers, dict):
        items = list(answers.items())
    elif isinstance(answers, list):
        items = [(pool[i]["id"], value) for i, value in enumerate(answers) if i < len(pool)]
    else:
        raise ValueError("answers doit être un objet {question_id: index} ou une liste d'index.")
    for qid, given in items:
        question = by_question.get(str(qid))
        if not question:
            continue
        try:
            given_index = int(given)
        except (TypeError, ValueError):
            given_index = -1
        ok = given_index == question["answer_index"]
        correct += int(ok)
        details.append(
            {
                "question_id": question["id"],
                "question": question["question"],
                "given": given_index,
                "expected": question["answer_index"],
                "correct": ok,
                "explanation": question["explanation"],
            }
        )
    total = len(details)
    score = round(100 * correct / total, 1) if total else 0.0
    passed = score >= 70
    weak = [d["question"] for d in details if not d["correct"]]
    feedback = (
        "Excellent, les notions clés sont maîtrisées. Passez au module suivant."
        if score >= 85
        else "Bon résultat. Revoyez les questions manquées avant de continuer."
        if passed
        else "Les bases doivent être consolidées. Reprenez le cours et refaites le quiz après révision."
    )
    return {
        "learner_id": learner["id"],
        "learner_name": learner["name"],
        "course_id": course["id"],
        "course_title": course["title"],
        "score": score,
        "correct": correct,
        "total": total,
        "passed": passed,
        "feedback": feedback,
        "details": details,
        "remediation": [f"Revoir : {q}" for q in weak[:3]],
    }


def _kpis() -> dict[str, Any]:
    learners_data = learners()
    attempts_data = attempts()
    courses_data = courses()
    delegations_data = delegations()
    scores = [int(a["score"]) for a in attempts_data]
    passed = [a for a in attempts_data if a["passed"] == "Oui"]
    completed_delegations = [d for d in delegations_data if d["status"] == "completed"]
    return {
        "learners": len(learners_data),
        "active_learners": sum(1 for l in learners_data if l["status"] == "Actif"),
        "courses": len(courses_data),
        "enrollments": sum(int(c["enrolled"]) for c in courses_data),
        "attempts": len(attempts_data),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "success_rate": round(100 * len(passed) / len(attempts_data), 1) if attempts_data else 0,
        "avg_completion": round(sum(c["completion_rate"] for c in courses_data) / len(courses_data), 1),
        "delegations": len(delegations_data),
        "delegation_success": round(100 * len(completed_delegations) / len(delegations_data), 1)
        if delegations_data
        else 0,
        "avg_latency_ms": round(
            sum(int(d["latency_ms"]) for d in delegations_data) / len(delegations_data), 0
        )
        if delegations_data
        else 0,
        "satisfaction": 4.6,
    }


def _score_distribution(scores: Iterable[int]) -> list[dict[str, Any]]:
    bins = [(0, 49), (50, 59), (60, 69), (70, 79), (80, 89), (90, 100)]
    labels = ["< 50", "50-59", "60-69", "70-79", "80-89", "90-100"]
    counts = Counter()
    for score in scores:
        for (low, high), label in zip(bins, labels):
            if low <= score <= high:
                counts[label] += 1
                break
    return [{"range": label, "count": counts[label]} for label in labels]


def learning_statistics(segment: str = "Tous") -> dict[str, Any]:
    """Calcule les KPI et les séries nécessaires aux graphiques du dashboard."""
    learners_data = learners()
    attempts_data = attempts()
    courses_data = courses()
    if segment and normalize(segment) not in ("tous", "toutes", "all"):
        learners_data = [l for l in learners_data if normalize(l["cohort"]) == normalize(segment)]
        allowed = {l["id"] for l in learners_data}
        attempts_data = [a for a in attempts_data if a["learner_id"] in allowed]
    by_cohort: dict[str, list[int]] = defaultdict(list)
    for learner in learners_data:
        learner_attempts = [int(a["score"]) for a in attempts_data if a["learner_id"] == learner["id"]]
        if learner_attempts:
            by_cohort[learner["cohort"]].append(round(sum(learner_attempts) / len(learner_attempts)))
    level_counts = Counter(l["level"] for l in learners_data)
    status_counts = Counter(l["status"] for l in learners_data)
    weekly: dict[str, list[int]] = defaultdict(list)
    for attempt in attempts_data:
        day = datetime.strptime(attempt["attempt_date"], "%Y-%m-%d")
        week = f"S{day.isocalendar().week:02d}"
        weekly[week].append(int(attempt["score"]))
    score_by_week = [
        {"week": week, "avg_score": round(sum(values) / len(values), 1), "attempts": len(values)}
        for week, values in sorted(weekly.items())
    ]
    enrollment_by_domain: dict[str, int] = defaultdict(int)
    for course in courses_data:
        enrollment_by_domain[domain_for(course["skills"][0])] += int(course["enrolled"])
    completion_by_course = sorted(
        [
            {
                "course_id": c["id"],
                "title": c["title"],
                "completion_rate": c["completion_rate"],
                "enrolled": c["enrolled"],
            }
            for c in courses_data
        ],
        key=lambda row: row["completion_rate"],
        reverse=True,
    )
    delegations_data = delegations()
    delegation_by_agent = []
    for agent in ("agent-tuteur", "agent-evaluation", "agent-orientation"):
        rows = [d for d in delegations_data if d["target"] == agent]
        delegation_by_agent.append(
            {
                "agent": agent,
                "delegations": len(rows),
                "success_rate": round(
                    100 * sum(1 for d in rows if d["status"] == "completed") / len(rows), 1
                )
                if rows
                else 0,
                "avg_latency_ms": round(sum(int(d["latency_ms"]) for d in rows) / len(rows)) if rows else 0,
            }
        )
    status_delegations = Counter(d["status"] for d in delegations_data)
    return {
        "segment": segment,
        "kpis": _kpis(),
        "by_level": [{"level": level, "count": count} for level, count in level_counts.most_common()],
        "by_status": [{"status": status, "count": count} for status, count in status_counts.items()],
        "by_cohort": [
            {"cohort": cohort, "avg_score": round(sum(vals) / len(vals), 1), "learners": len(vals)}
            for cohort, vals in sorted(by_cohort.items())
        ],
        "score_by_week": score_by_week,
        "score_distribution": _score_distribution([int(a["score"]) for a in attempts_data]),
        "enrollment_by_domain": [
            {"domain": domain, "enrolled": enrolled}
            for domain, enrolled in sorted(enrollment_by_domain.items(), key=lambda x: -x[1])
        ],
        "completion_by_course": completion_by_course,
        "delegation_by_agent": delegation_by_agent,
        "delegation_status": [{"status": s, "count": c} for s, c in status_delegations.items()],
        "recent_attempts": sorted(
            attempts_data, key=lambda a: a["attempt_date"], reverse=True
        )[:12],
    }


def storage_status() -> dict[str, Any]:
    """Indique le backend de données actif (MongoDB Atlas ou JSON local)."""
    status = mongo_store.health()
    status["mongo_uri_configured"] = bool(mongo_store.URI)
    status["json_fallback"] = True
    return status


def list_tools() -> list[dict[str, Any]]:
    """Liste lisible des outils MCP exposés (utilisée par le dashboard)."""
    return [
        {
            "name": "search_courses",
            "title": "Rechercher des cours",
            "description": "Recherche dans le catalogue EdTech par mots-clés, compétence ou niveau.",
        },
        {
            "name": "get_learner_profile",
            "title": "Profil apprenant",
            "description": "Retourne le niveau, l'objectif, la progression et les cours validés.",
        },
        {
            "name": "recommend_learning_path",
            "title": "Parcours recommandé",
            "description": "Construit un parcours ordonné, prérequis inclus, vers une compétence cible.",
        },
        {
            "name": "generate_quiz",
            "title": "Générer un quiz",
            "description": "Crée un quiz formatif à partir de la banque de questions du cours.",
        },
        {
            "name": "grade_quiz",
            "title": "Corriger un quiz",
            "description": "Calcule le score, les corrections et un feedback de remédiation.",
        },
        {
            "name": "get_learning_statistics",
            "title": "Statistiques d'apprentissage",
            "description": "Agrège les KPI et les séries pour le dashboard (scores, cohortes, complétion).",
        },
    ]


if __name__ == "__main__":
    print(json.dumps(learning_statistics(), ensure_ascii=False, indent=2)[:2000])
