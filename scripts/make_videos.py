# -*- coding: utf-8 -*-
"""Génère les trois vidéos EduAgentic : J33, J34 et finale.

- narration française avec Edge TTS (repli SAPI) ;
- images de slides, schémas et captures du dashboard ;
- montage H.264/AAC 1920x1080 avec ffmpeg.
"""
from __future__ import annotations

import asyncio
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import edge_tts
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SHOTS = ROOT / "screenshots"
VIDEOS = ROOT / "videos"
DOCS = ROOT / "docs"
PRES = ROOT / "presentation"
FRAMES = VIDEOS / "_frames"
AUDIO = VIDEOS / "_audio"
SEGMENTS = VIDEOS / "_segments"
for folder in (VIDEOS, FRAMES, AUDIO, SEGMENTS):
    folder.mkdir(exist_ok=True)

FFMPEG = r"C:\Users\HP\AppData\Local\Python\pythoncore-3.15-64\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"
NAVY = (11, 35, 64)
GOLD = (244, 180, 0)
WHITE = (255, 255, 255)
MUTED = (185, 204, 224)

VOICE_J33 = "fr-FR-DeniseNeural"
VOICE_J34 = "fr-FR-HenriNeural"
VOICE_FINAL = "fr-FR-DeniseNeural"


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=capture, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Commande échouée : {' '.join(cmd[:4])}\n{result.stderr[-800:] if result.stderr else ''}")
    return result


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        return 3.0
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def sapi_fallback(text: str, path: Path) -> None:
    import win32com.client

    voice = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open(str(path.with_suffix(".wav")), 3, False)
    voice.AudioOutputStream = stream
    voice.Speak(text)
    stream.Close()
    run([FFMPEG, "-y", "-i", str(path.with_suffix(".wav")), "-c:a", "aac", "-b:a", "192k", str(path)])


async def _edge(text: str, path: Path, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice, rate="-5%", volume="+0%")
    await communicate.save(str(path))


def synth(text: str, path: Path, voice: str) -> float:
    if path.exists() and path.stat().st_size > 1000:
        return probe_duration(path)
    try:
        asyncio.run(_edge(text, path, voice))
    except Exception as exc:  # noqa: BLE001
        print("  TTS Edge indisponible, repli SAPI :", type(exc).__name__)
        sapi_fallback(text, path)
    return probe_duration(path)


def fit_image(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    img = img.convert("RGB")
    ratio = min(max_w / img.width, max_h / img.height)
    return img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)


def compose_frame(image_path: Path, title: str, subtitle: str, day: str, out: Path) -> None:
    canvas = Image.new("RGB", (1920, 1080), NAVY)
    draw = ImageDraw.Draw(canvas)
    # bandeau haut
    draw.rectangle((0, 0, 1920, 96), fill=(8, 26, 48))
    logo = Image.open(ASSETS / "logo.png").convert("RGBA")
    logo = logo.resize((300, 79), Image.LANCZOS)
    canvas.paste(logo, (48, 8), logo)
    f_title = ImageFont.truetype(FONT_BOLD, 32)
    f_sub = ImageFont.truetype(FONT_REG, 20)
    f_day = ImageFont.truetype(FONT_BOLD, 20)
    draw.text((390, 22), title, font=f_title, fill=WHITE)
    draw.text((392, 62), subtitle, font=f_sub, fill=MUTED)
    # badge
    draw.rounded_rectangle((1720, 26, 1870, 68), radius=21, fill=GOLD)
    draw.text((1753, 36), day, font=f_day, fill=NAVY)
    # image
    img = fit_image(Image.open(image_path), 1800, 870)
    x = (1920 - img.width) // 2
    y = 120 + (870 - img.height) // 2
    draw.rounded_rectangle((x - 8, y - 8, x + img.width + 8, y + img.height + 8), radius=14, fill=(255, 255, 255))
    canvas.paste(img, (x, y))
    # pied
    draw.line((48, 1025, 1872, 1025), fill=(42, 82, 119), width=2)
    f_foot = ImageFont.truetype(FONT_REG, 18)
    draw.text((50, 1040), "EduAgentic · Agentic AI in Education Technology · données synthétiques", font=f_foot, fill=MUTED)
    draw.text((1725, 1040), "localhost:8011", font=f_foot, fill=MUTED)
    canvas.save(out)


def segment(image: Path, audio: Path, out: Path) -> None:
    duration = probe_duration(audio) + 0.45
    video_filter = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0B2340,format=yuv420p"
    )
    run(
        [
            FFMPEG,
            "-y",
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-t",
            f"{duration:.3f}",
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-shortest",
            str(out),
        ]
    )


def concat(segments: list[Path], out: Path) -> None:
    list_file = VIDEOS / "_concat.txt"
    list_file.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(out),
        ]
    )


def build_day(
    name: str,
    voice: str,
    items: list[tuple[str, Path, str, str, str]],
    day: str,
) -> Path:
    """items = (kind, image, titre, sous-titre, narration), kind = slide|frame."""
    print(f"Construction de {name}…")
    ordered: list[tuple[Path, str]] = []
    for idx, (kind, image_path, title, subtitle, narration) in enumerate(items, 1):
        if kind == "frame":
            image_path = FRAMES / f"{name}_{idx:02d}.png"
            compose_frame(items[idx - 1][1], title, subtitle, day, image_path)
        audio = AUDIO / f"{name}_{idx:02d}.mp3"
        print(f"  {idx:02d} · {title} · {synth(narration, audio, voice):.1f}s")
        ordered.append((image_path, audio))
    segments = []
    for i, (image_path, audio) in enumerate(ordered, 1):
        seg = SEGMENTS / f"{name}_{i:02d}.mp4"
        segment(image_path, audio, seg)
        segments.append(seg)
    out = VIDEOS / f"{name}.mp4"
    concat(segments, out)
    print("  →", out.name, f"{out.stat().st_size/1024/1024:.1f} Mo", f"{sum(probe_duration(s) for s in segments)/60:.1f} min")
    return out


def render_slides(pdf: Path, prefix: str) -> list[Path]:
    doc = fitz.open(pdf)
    paths = []
    for i, page in enumerate(doc, 1):
        zoom = 1920 / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        out = FRAMES / f"{prefix}_{i:02d}.png"
        pix.save(out)
        paths.append(out)
    return paths


def build_final() -> Path:
    print("Construction de la vidéo finale…")
    slides = render_slides(PRES / "Presentation_Finale_J33_J34.pdf", "final_slide")
    prs = Presentation(PRES / "Presentation_Finale_J33_J34.pptx")
    narrations = []
    for i, slide in enumerate(prs.slides, 1):
        text = ""
        if slide.has_notes_slide:
            text = slide.notes_slide.notes_text_frame.text.strip()
        narrations.append(text or f"Diapositive {i} de la synthèse EduAgentic.")
    segments = []
    for i, (image_path, text) in enumerate(zip(slides, narrations), 1):
        audio = AUDIO / f"final_{i:02d}.mp3"
        print(f"  {i:02d} · {synth(text, audio, VOICE_FINAL):.1f}s")
        seg = SEGMENTS / f"final_{i:02d}.mp4"
        segment(image_path, audio, seg)
        segments.append(seg)
    out = VIDEOS / "Video_Finale_Agentic_AI_EdTech.mp4"
    concat(segments, out)
    print("  →", out.name, f"{out.stat().st_size/1024/1024:.1f} Mo", f"{sum(probe_duration(s) for s in segments)/60:.1f} min")
    return out


def main() -> None:
    j33 = render_slides(PRES / "J33_MCP_Presentation.pdf", "j33_slide")
    j33_items = [
        ("slide", j33[0], "Couverture", "", "Bienvenue dans le mini-projet du jour 33. Nous allons construire un serveur MCP pour une plateforme d'apprentissage, le connecter à un agent Langflow, puis observer chaque appel dans un playground."),
        ("slide", j33[1], "Le constat", "", "Le constat est simple. Chaque outil possède sa propre API, ses formats et son authentification. Chaque nouvelle intégration ajoute du code et de la maintenance. MCP propose un langage commun pour que l'agent et les outils se comprennent."),
        ("slide", j33[2], "Le concept", "", "Avant MCP, le client connaît toutes les routes. Après MCP, le serveur publie ses outils avec leurs schémas. L'agent découvre, choisit et reçoit un résultat structuré, sans connaître l'implémentation."),
        ("frame", ASSETS / "architecture_mcp.png", "Architecture MCP", "Utilisateur, agent, serveur MCP, données : un cycle lisible", "L'architecture tient en quatre composants : le playground, l'agent, le serveur MCP et les données EdTech. L'agent appelle list_tools, choisit le bon outil, le serveur exécute et retourne un JSON. Le dashboard observe le cycle et conserve la trace."),
        ("frame", ASSETS / "workflow_mcp.png", "Workflow Langflow", "Chat Input → Agent → MCP Tools → Chat Output", "Dans Langflow, le workflow contient quatre nœuds : Chat Input, Agent, MCP Tools et Chat Output. Le composant MCP Tools est connecté au serveur edumcp-edtech en SSE. Le JSON final est fourni et prêt à importer."),
        ("frame", SHOTS / "mcp_result.png", "Playground MCP", "Profil, parcours recommandé et ressources", "Voici le playground. Nous demandons le parcours de Lina vers Data Analyst. L'agent appelle trois outils : profil, recommandation de parcours et recherche de cours. La réponse affiche les trois étapes, les prérequis et les ressources."),
        ("frame", SHOTS / "mcp_result.png", "Trace d'exécution", "Outil, arguments, latence, résultat", "La trace montre l'outil choisi, les arguments, la latence et le résultat complet. C'est ce qui rend la démonstration vérifiable : on ne voit pas seulement la réponse, on voit comment elle a été produite."),
        ("slide", j33[7], "Résultats", "", "Les tests confirment six outils exposés, un handshake MCP réussi et des appels sans erreur. La latence reste faible en local. Le dashboard affiche les mêmes données sous forme de KPI et de graphiques."),
        ("slide", j33[8], "Sécurité et limites", "", "Le projet est sûr par construction : données synthétiques, serveur local et outils en lecture. Pour une production, il faudrait ajouter l'authentification, le chiffrement, la gestion RGPD et une évaluation du modèle."),
        ("slide", j33[9], "Conclusion", "", "En conclusion, MCP outille l'agent. Le jour 34 ajoute A2A pour faire collaborer plusieurs agents spécialisés. Les deux protocoles sont complémentaires."),
    ]
    build_day("J33_MCP_Workflow_Playground", VOICE_J33, j33_items, "J33")

    j34 = render_slides(PRES / "J34_A2A_Presentation.pdf", "j34_slide")
    j34_items = [
        ("slide", j34[0], "Couverture", "", "Bienvenue dans le jour 34. Nous allons faire collaborer trois agents spécialisés avec le protocole A2A : découverte, délégation et traçabilité."),
        ("slide", j34[1], "Pourquoi A2A", "", "Un agent seul ne possède pas toutes les compétences. A2A repose sur trois piliers : l'AgentCard, la découverte et la délégation. Chaque agent publie ce qu'il sait faire et comment le joindre."),
        ("slide", j34[2], "Les agents", "", "Nous avons trois spécialistes : le Tuteur pour les cours et le parcours, l'Évaluation pour les quiz et le feedback, l'Orientation pour les compétences et le métier. L'orchestrateur sélectionne et agrège."),
        ("frame", ASSETS / "architecture_a2a.png", "Architecture A2A", "Découvrir les cartes, déléguer, agréger", "L'orchestrateur découvre les cartes, envoie trois messages JSON-RPC en parallèle et agrège les artifacts. Chaque demande porte un correlation_id unique."),
        ("slide", j34[5], "Protocole", "", "Le protocole utilise JSON-RPC 2.0. Un message contient les parts textuelles, un contextId et des metadata. La réponse est une Task avec un statut et des artifacts."),
        ("frame", ASSETS / "workflow_a2a.png", "Workflow Langflow", "Découverte → Orchestrateur → 3 agents → Chat Output", "Le workflow Langflow reprend cette logique : Chat Input, découverte, orchestrateur, trois agents et Chat Output. Le JSON final est fourni avec le projet."),
        ("frame", SHOTS / "a2a_result.png", "Dashboard A2A", "Une demande, trois agents, une synthèse", "Dans le dashboard, on lance une orchestration pour Lina. Les trois agents répondent en parallèle : parcours, ressources et quiz. La réponse est consolidée en une synthèse."),
        ("frame", SHOTS / "a2a_timeline.png", "Timeline de délégation", "Statut, transport, latence, correlation_id", "La timeline montre chaque délégation avec son statut, son transport et sa latence. Le correlation_id relie les trois échanges à la demande initiale. Les logs sont persistés."),
        ("slide", j34[9], "Résultats", "", "Les résultats sont conformes : trois agents découverts, trois délégations complétées, trois artifacts. Les limites sont connues : pas de signature de carte, pas de retry, pas de streaming."),
        ("slide", j34[10], "Conclusion", "", "En conclusion, A2A transforme trois agents spécialisés en une équipe traçable. MCP outille, A2A coordonne, le dashboard prouve."),
    ]
    build_day("J34_A2A_Workflow_Playground", VOICE_J34, j34_items, "J34")
    build_final()
    print("Vidéos terminées.")


if __name__ == "__main__":
    main()
