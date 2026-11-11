# -*- coding: utf-8 -*-
"""Publie le dépôt sur GitHub avec les identifiants stockés par Git.

Le token n'est jamais affiché. Le fichier .env est exclu par .gitignore.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REPO = "Agentic-AI-EdTech-J33-J34"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def credentials() -> tuple[str, str]:
    result = subprocess.run(
        ["git", "credential", "fill"],
        cwd=ROOT,
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=True,
    )
    data = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data.get("username", ""), data.get("password", "")


def main() -> None:
    if not (ROOT / ".git").exists():
        git("init")
        git("branch", "-M", "main")
    git("add", "-A")
    status = git("status", "--short").stdout
    if status.strip():
        git("commit", "-m", "EduAgentic J33/J34 — MCP & A2A, correction finale")
    user, token = credentials()
    if not user or not token:
        print("Identifiants GitHub introuvables. Dépôt local prêt ; voir GITHUB.md.")
        return
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    me = requests.get("https://api.github.com/user", headers=headers, timeout=20)
    if me.status_code != 200:
        print("Token GitHub non valide ou expiré.")
        return
    login = me.json()["login"]
    existing = requests.get(f"https://api.github.com/repos/{login}/{REPO}", headers=headers, timeout=20)
    if existing.status_code == 404:
        created = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json={
                "name": REPO,
                "description": "EduAgentic — MCP & A2A pour l'éducation (J33/J34), dashboard 8011, documentation et vidéos.",
                "private": False,
                "has_issues": True,
                "has_wiki": False,
                "has_projects": False,
            },
            timeout=30,
        )
        if created.status_code not in (201, 200):
            print("Création du dépôt impossible :", created.status_code, created.json().get("message", ""))
            return
        print("Dépôt créé :", created.json()["html_url"])
    else:
        print("Dépôt existant :", existing.json()["html_url"])
    url = f"https://github.com/{login}/{REPO}.git"
    remotes = git("remote", check=False).stdout
    if "origin" in remotes:
        git("remote", "set-url", "origin", url)
    else:
        git("remote", "add", "origin", url)
    push = git("push", "-u", "origin", "main", check=False)
    if push.returncode == 0:
        print("Push OK :", f"https://github.com/{login}/{REPO}")
    else:
        print("Push à finaliser manuellement :", (push.stderr or push.stdout).strip()[-500:])
        print("Voir GITHUB.md")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print("Erreur Git :", (exc.stderr or exc.stdout or "")[-600:])
        sys.exit(1)
