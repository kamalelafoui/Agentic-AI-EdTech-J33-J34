# -*- coding: utf-8 -*-
"""Backend MongoDB Atlas optionnel pour EduAgentic.

- Les données sont stockées dans des collections préfixées `edtech_`.
- Les collections existantes de la base ne sont jamais modifiées.
- Si Atlas est indisponible, `edtech_core` bascule automatiquement sur JSON/CSV.
- L'URI est lue dans .env et n'est jamais affichée ni journalisée.
"""
from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

BACKEND = os.environ.get("EDTECH_BACKEND", "json").strip().lower()
URI = os.environ.get("MONGODB_URI", "").strip()
DB_NAME = os.environ.get("MONGODB_DB", "fusion").strip()
PREFIX = os.environ.get("MONGODB_COLLECTION_PREFIX", "edtech_").strip()
COLLECTIONS = {
    "courses": f"{PREFIX}courses",
    "learners": f"{PREFIX}learners",
    "quiz_bank": f"{PREFIX}quiz_bank",
    "quiz_attempts": f"{PREFIX}quiz_attempts",
    "a2a_delegations": f"{PREFIX}a2a_delegations",
    "meta": f"{PREFIX}meta",
}

_client = None
_db = None
_last_error = ""
_failed_until = 0.0
_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
CACHE_TTL = 4.0


def enabled() -> bool:
    return BACKEND in ("mongo", "mongodb", "atlas") and bool(URI)


def get_db():
    global _client, _db, _last_error, _failed_until
    if not enabled():
        return None
    if _db is not None:
        return _db
    if time.time() < _failed_until:
        return None
    try:
        from pymongo import MongoClient

        _client = MongoClient(
            URI,
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000,
            socketTimeoutMS=8000,
            maxPoolSize=10,
            appname="EduAgentic",
        )
        _client.admin.command("ping")
        _db = _client[DB_NAME]
        _last_error = ""
        return _db
    except Exception as exc:  # noqa: BLE001
        _last_error = type(exc).__name__
        _failed_until = time.time() + 30
        _db = None
        return None


def _read_json(name: str) -> list[dict[str, Any]]:
    with (DATA / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _seed() -> None:
    db = get_db()
    if db is None:
        return
    try:
        if db[COLLECTIONS["courses"]].estimated_document_count() == 0:
            docs = _read_json("courses.json")
            if docs:
                db[COLLECTIONS["courses"]].insert_many([dict(d) for d in docs])
            db[COLLECTIONS["courses"]].create_index("id", unique=True)
            db[COLLECTIONS["courses"]].create_index("skills")
        if db[COLLECTIONS["learners"]].estimated_document_count() == 0:
            docs = _read_json("learners.json")
            if docs:
                db[COLLECTIONS["learners"]].insert_many([dict(d) for d in docs])
            db[COLLECTIONS["learners"]].create_index("id", unique=True)
            db[COLLECTIONS["learners"]].create_index("cohort")
        if db[COLLECTIONS["quiz_bank"]].estimated_document_count() == 0:
            docs = _read_json("quiz_bank.json")
            if docs:
                db[COLLECTIONS["quiz_bank"]].insert_many([dict(d) for d in docs])
            db[COLLECTIONS["quiz_bank"]].create_index("id", unique=True)
            db[COLLECTIONS["quiz_bank"]].create_index("course_id")
        if db[COLLECTIONS["quiz_attempts"]].estimated_document_count() == 0:
            rows = _read_csv("quiz_attempts.csv")
            for row in rows:
                row["score"] = int(row["score"])
                row["duration_min"] = int(row["duration_min"])
            if rows:
                db[COLLECTIONS["quiz_attempts"]].insert_many(rows)
            db[COLLECTIONS["quiz_attempts"]].create_index("learner_id")
            db[COLLECTIONS["quiz_attempts"]].create_index("attempt_date")
        if db[COLLECTIONS["a2a_delegations"]].estimated_document_count() == 0:
            rows = _read_csv("a2a_delegations.csv")
            for row in rows:
                row["latency_ms"] = int(row["latency_ms"])
            if rows:
                db[COLLECTIONS["a2a_delegations"]].insert_many(rows)
            db[COLLECTIONS["a2a_delegations"]].create_index("target")
            db[COLLECTIONS["a2a_delegations"]].create_index("correlation_id")
        db[COLLECTIONS["meta"]].update_one(
            {"_id": "config"},
            {
                "$set": {
                    "project": "EduAgentic J33/J34",
                    "dataset": "synthetic",
                    "seeded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
            },
            upsert=True,
        )
    except Exception as exc:  # noqa: BLE001
        global _last_error, _failed_until
        _last_error = type(exc).__name__
        _failed_until = time.time() + 30


def read(name: str) -> list[dict[str, Any]] | None:
    """Lit une collection ; None si le backend Mongo est indisponible."""
    if not enabled():
        return None
    now = time.time()
    cached = _cache.get(name)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]
    db = get_db()
    if db is None:
        return None
    try:
        if db[COLLECTIONS[name]].estimated_document_count() == 0:
            _seed()
        docs = list(db[COLLECTIONS[name]].find({}, {"_id": 0}))
        _cache[name] = (now, docs)
        return docs
    except Exception as exc:  # noqa: BLE001
        global _last_error, _failed_until
        _last_error = type(exc).__name__
        _failed_until = time.time() + 30
        return None


def record_attempt(row: dict[str, Any]) -> bool:
    """Insère une tentative de quiz dans Atlas (optionnel)."""
    if not enabled() or os.environ.get("EDTECH_WRITE_ATTEMPTS", "0") != "1":
        return False
    db = get_db()
    if db is None:
        return False
    try:
        db[COLLECTIONS["quiz_attempts"]].insert_one(dict(row))
        _cache.pop("quiz_attempts", None)
        return True
    except Exception:  # noqa: BLE001
        return False


def health() -> dict[str, Any]:
    db = get_db()
    if db is None:
        return {
            "backend": "json",
            "mongo": False,
            "reason": _last_error or "désactivé",
            "db": DB_NAME,
        }
    try:
        counts = {name: db[COLLECTIONS[name]].estimated_document_count() for name in COLLECTIONS}
        return {
            "backend": "mongodb",
            "mongo": True,
            "db": DB_NAME,
            "prefix": PREFIX,
            "counts": counts,
        }
    except Exception as exc:  # noqa: BLE001
        return {"backend": "mongodb", "mongo": True, "db": DB_NAME, "error": type(exc).__name__}


def reset_cache() -> None:
    _cache.clear()
