# -*- coding: utf-8 -*-
"""Crée l'archive finale en excluant les secrets et les fichiers temporaires."""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Agentic_AI_EdTech_J33_J34_FINAL.zip"

ROOT_FILES = [
    "README.md",
    "LIVRABLES.md",
    "GITHUB.md",
    "LICENSE",
    "MANIFEST.txt",
    "requirements.txt",
    "requirements-dev.txt",
    "start_demo.ps1",
    ".env.example",
    ".gitignore",
    ".streamlit/config.toml",
]
DIRS = ["assets", "a2a", "dashboard", "data", "docs", "json", "mcp_server", "presentation", "shared", "scripts", "screenshots", "videos"]
EXCLUDED_NAMES = {".env", ".git", "__pycache__", "logs", "_frames", "_audio", "_segments"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
EXCLUDED_FILES = {"a2a_live.jsonl", "_concat.txt"}


def included(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_NAMES:
        return False
    if path.name in EXCLUDED_FILES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.name.startswith("_") and path.parent.name == "videos":
        return False
    return True


def main() -> None:
    files: list[Path] = []
    for name in ROOT_FILES:
        path = ROOT / name
        if path.exists():
            files.append(path)
    for dirname in DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and included(path):
                files.append(path)
    files = sorted(set(files), key=lambda p: str(p.relative_to(ROOT)).lower())
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in files:
            zf.write(path, path.relative_to(ROOT).as_posix())
    total = OUT.stat().st_size / (1024 * 1024)
    print(f"Archive : {OUT.name} · {len(files)} fichiers · {total:.1f} Mo")
    print("Vérification : .env exclu =", all(p.name != ".env" for p in files))


if __name__ == "__main__":
    main()
