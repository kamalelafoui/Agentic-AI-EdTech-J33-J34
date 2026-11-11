# -*- coding: utf-8 -*-
"""Test de connexion MongoDB Atlas sans afficher l'URI."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_env()
    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        print("MONGODB_URI absent")
        sys.exit(2)
    client = MongoClient(uri, serverSelectionTimeoutMS=8000, connectTimeoutMS=8000)
    try:
        pong = client.admin.command("ping")
        print("ping:", pong.get("ok"))
        print("database:", os.environ.get("MONGODB_DB", "fusion"))
        db = client[os.environ.get("MONGODB_DB", "fusion")]
        print("collections:", db.list_collection_names())
        print("server:", client.address)
    except PyMongoError as exc:
        print("ERREUR MongoDB:", type(exc).__name__, str(exc)[:300])
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
