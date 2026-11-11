# -*- coding: utf-8 -*-
"""Génère les présentations PPTX J33, J34 et finale, puis les exporte en PDF."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

from pptx_helpers import (  # noqa: E402
    ASSETS,
    BLUE,
    BODY_FONT,
    BORDER,
    GOLD,
    GREEN,
    INK,
    LIGHT,
    MUTED,
    NAVY,
    PURPLE,
    SOFT_GOLD,
    TEAL,
    TITLE_FONT,
    WHITE,
    bg,
    blank,
    card,
    code,
    cover,
    footer,
    header,
    image,
    line,
    new_deck,
    notes,
    paragraphs,
    pill,
    rect,
    rich,
    section,
    stat,
    table,
    txt,
)

DECK_DIR = ROOT / "presentation"
DECK_DIR.mkdir(exist_ok=True)
SHOTS = ROOT / "screenshots"
BENCH = ROOT / "data" / "benchmarks.json"


def benchmark() -> dict:
    try:
        return json.loads(BENCH.read_text(encoding="utf-8"))
    except Exception:
        return {"mcp_median_ms": 17.8, "a2a_latency_ms": 189.0}


BENCH_DATA = benchmark()
MCP_MS = f"{BENCH_DATA['mcp_median_ms']:.1f}".replace(".", ",")
A2A_MS = f"{BENCH_DATA['a2a_latency_ms']:.0f}"


def add_j33() -> Path:
    prs = new_deck()
    total = 11
    # 1 — couverture
    cover(
        prs,
        "Jour 33 · Mini-projet · Correction finale",
        "MCP en EdTech :\nexposer des outils, augmenter un agent",
        "Serveur FastMCP, workflow Langflow et playground localhost:8011",
        "Kamal El Afoui · Centre des Très Petites Entreprises Solidaires / DBA Technology · 11 novembre 2026",
        ["6 outils MCP", "Workflow Langflow", "Playground"],
    )
    notes(
        prs.slides[-1],
        "Bonjour. Cette présentation couvre le mini-projet du jour 33 : construire un serveur MCP, "
        "le connecter à un agent Langflow et démontrer le tout dans un playground. L'objectif est de montrer "
        "comment un agent découvre et utilise des outils EdTech sans connaître leur implémentation.",
    )

    # 2 — problème
    s = blank(prs)
    header(s, "01 · Le constat", "Chaque outil est une intégration spécifique", "J33")
    problems = [
        ("API REST", "Chaque fournisseur a ses routes, ses formats et ses règles.", BLUE, "{}"),
        ("Connecteurs", "Le code de l'agent dépend de chaque source de données.", PURPLE, "🔌"),
        ("Formats", "JSON, CSV, texte libre : l'agent doit tout normaliser.", GOLD, "📄"),
        ("Authentification", "Clé API, OAuth, token interne : rien n'est unifié.", TEAL, "🔐"),
    ]
    for i, (title, body, accent, icon) in enumerate(problems):
        card(s, 0.65 + i * 3.08, 2.05, 2.88, 2.25, title, body, accent, icon)
    rect(s, 0.65, 4.75, 12.05, 1.25, NAVY, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 4.95, 11.4, 0.4, "Conséquence : chaque nouvelle intégration demande du développement et de la maintenance.",
        15, WHITE, True)
    txt(s, 0.95, 5.38, 11.4, 0.3, "MCP propose un langage commun pour que l'agent et les outils se comprennent.",
        11, GOLD)
    footer(s, 2, total)
    notes(
        s,
        "Aujourd'hui, chaque agent se connecte aux outils avec sa propre méthode. Les API, les formats et "
        "l'authentification changent à chaque fois. Résultat : beaucoup de code spécifique et une maintenance "
        "difficile. MCP arrive pour standardiser cette connexion.",
    )

    # 3 — concept
    s = blank(prs)
    header(s, "02 · Le concept", "MCP : un contrat standard entre l'agent et les outils", "J33")
    rect(s, 0.65, 2.0, 5.85, 3.7, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 2.2, 5.2, 0.35, "AVANT", 10, MUTED, True, char_spacing=2)
    txt(s, 0.95, 2.6, 5.2, 0.45, "Chaque outil = une intégration", 18, NAVY, True)
    paragraphs(
        s,
        0.95,
        3.2,
        5.15,
        2.2,
        [
            ("API propre : ", "une route par fournisseur."),
            ("Client rigide : ", "il connaît toutes les routes à l'avance."),
            ("Évolution coûteuse : ", "chaque version casse le client."),
        ],
        11.5,
        space_after=6,
    )
    rect(s, 6.75, 2.0, 5.95, 3.7, NAVY, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 7.05, 2.2, 5.3, 0.35, "APRÈS", 10, GOLD, True, char_spacing=2)
    txt(s, 7.05, 2.6, 5.3, 0.45, "Un serveur publie ses outils", 18, WHITE, True)
    paragraphs(
        s,
        7.05,
        3.2,
        5.2,
        2.2,
        [
            ("Découverte : ", "l'agent lit la liste des outils."),
            ("Sélection : ", "il choisit selon la demande."),
            ("Exécution : ", "il reçoit un résultat structuré."),
        ],
        11.5,
        WHITE,
        GOLD,
        space_after=6,
        lead_color=WHITE,
    )
    txt(s, 0.65, 5.95, 12.05, 0.5, "Le serveur expose des tools, des resources et des prompts. L'agent reste concentré sur la décision.",
        11.5, MUTED)
    footer(s, 3, total)
    notes(
        s,
        "Avant MCP, le client connaît toutes les routes et chaque évolution casse l'intégration. Après MCP, "
        "le serveur publie une liste d'outils avec leurs schémas ; l'agent découvre, choisit et appelle. "
        "C'est le même principe qu'un catalogue de fonctions standardisées.",
    )

    # 4 — architecture
    s = blank(prs)
    header(s, "03 · Architecture", "Quatre composants, un cycle d'appel lisible", "J33")
    image(s, ASSETS / "architecture_mcp.png", 0.55, 1.55, w=9.35)
    rect(s, 10.15, 1.75, 2.65, 4.95, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 10.4, 1.95, 2.15, 0.3, "LE CYCLE", 9, GOLD, True, char_spacing=2)
    steps = [
        ("1", "Découverte", "list_tools"),
        ("2", "Sélection", "le LLM choisit"),
        ("3", "Exécution", "call_tool"),
        ("4", "Synthèse", "réponse en français"),
    ]
    yy = 2.35
    for num, label, sub in steps:
        pill(s, 10.4, yy, 0.42, 0.42, num, NAVY, WHITE, 11)
        txt(s, 10.95, yy - 0.02, 1.7, 0.3, label, 11, NAVY, True)
        txt(s, 10.95, yy + 0.26, 1.7, 0.25, sub, 8.5, MUTED)
        yy += 0.95
    txt(s, 10.4, 6.0, 2.1, 0.5, "Le JSON brut reste côté serveur.", 9, TEAL, True)
    footer(s, 4, total)
    notes(
        s,
        "L'architecture tient en quatre composants : le playground ou Langflow, l'agent, le serveur MCP et les "
        "données EdTech. L'agent découvre les outils, choisit le bon, le serveur exécute et retourne un résultat "
        "structuré. Le dashboard observe le cycle et conserve la trace.",
    )

    # 5 — outils
    s = blank(prs)
    header(s, "04 · Le serveur", "Six outils pour couvrir le parcours d'apprentissage", "J33")
    tools = [
        ("search_courses", "Recherche un cours par mots-clés, niveau ou compétence.", "🔎", BLUE),
        ("get_learner_profile", "Lit le niveau, l'objectif, la progression et les cours validés.", "👤",  TEAL),
        ("recommend_learning_path", "Construit un parcours ordonné, prérequis inclus.", "🧭", GOLD),
        ("generate_quiz", "Génère un quiz formatif sans révéler les réponses.", "📝", PURPLE),
        ("grade_quiz", "Corrige, calcule le score et propose une remédiation.", "✅", GREEN),
        ("get_learning_statistics", "Agrège les KPI et les séries du dashboard.", "📊", NAVY),
    ]
    for i, (name, desc, icon, accent) in enumerate(tools):
        x = 0.65 + (i % 3) * 4.08
        y = 2.0 + (i // 3) * 2.08
        card(s, x, y, 3.87, 1.82, name, desc, accent, icon, body_size=10.5, title_size=12)
    txt(s, 0.65, 6.15, 12.05, 0.5, "Chaque outil est découvert via list_tools et décrit par un schéma JSON généré par FastMCP. Données : MongoDB Atlas (edtech_*) ou JSON local.",
        10, MUTED)
    footer(s, 5, total)
    notes(
        s,
        "Le serveur expose six outils. Trois concernent la recherche et la personnalisation, deux concernent "
        "l'évaluation, un concerne le pilotage. Chaque outil possède une docstring qui devient un schéma JSON : "
        "c'est ce schéma que l'agent lit pour choisir.",
    )

    # 6 — workflow
    s = blank(prs)
    header(s, "05 · Langflow", "Le workflow : Chat Input → Agent → MCP Tools → Chat Output", "J33")
    image(s, ASSETS / "workflow_mcp.png", 0.55, 1.55, w=9.55)
    rect(s, 10.35, 1.8, 2.4, 4.8, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 10.55, 2.0, 2.0, 0.3, "CONFIGURATION", 8.5, GOLD, True, char_spacing=1.5)
    config = [
        ("Serveur", "edumcp-edtech"),
        ("Transport", "SSE"),
        ("URL", "127.0.0.1:8000/sse"),
        ("Modèle", "à configurer"),
        ("Max iter.", "15"),
    ]
    yy = 2.42
    for key, value in config:
        txt(s, 10.55, yy, 1.9, 0.22, key.upper(), 7, MUTED, True)
        txt(s, 10.55, yy + 0.2, 1.95, 0.3, value, 9, NAVY, True)
        yy += 0.68
    footer(s, 6, total)
    notes(
        s,
        "Le workflow Langflow contient quatre nœuds. Le Chat Input reçoit la question, l'Agent analyse, "
        "MCP Tools découvre et appelle les outils, Chat Output affiche la réponse. Le JSON final est fourni ; "
        "il suffit de déclarer le serveur MCP en SSE avant l'import.",
    )

    # 7 — playground
    s = blank(prs)
    header(s, "06 · Démonstration", "Le playground rend chaque appel observable", "J33")
    if (SHOTS / "mcp_result2.png").exists():
        image(s, SHOTS / "mcp_result2.png", 0.45, 1.55, w=8.1)
    rect(s, 8.85, 1.7, 3.95, 4.95, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 9.1, 1.9, 3.4, 0.3, "TRACE D'EXÉCUTION", 8.5, GOLD, True, char_spacing=1.5)
    paragraphs(
        s,
        9.1,
        2.3,
        3.45,
        4.1,
        [
            ("Outil choisi : ", "search_courses, recommend_learning_path, generate_quiz."),
            ("Arguments : ", "visibles en JSON pour chaque appel."),
            ("Latence : ", "mesurée et affichée par outil."),
            ("Résultat : ", "inspectable dans un bloc JSON."),
            ("Réponse : ", "reformulée en français, sans JSON brut."),
        ],
        10,
        space_after=6,
    )
    footer(s, 7, total)
    notes(
        s,
        "Le playground montre le profil, le parcours recommandé et les ressources. À droite, la trace donne "
        "l'outil, les arguments, la latence et le résultat. C'est ce qui rend la démonstration crédible : "
        "on ne voit pas seulement la réponse, on voit comment elle a été produite.",
    )

    # 8 — résultats
    s = blank(prs)
    header(s, "07 · Résultats", "Six outils testés, une latence maîtrisée", "J33")
    stats = [
        ("6 / 6", "outils exposés", TEAL, "list_tools"),
        (f"{MCP_MS} ms", "latence médiane", GOLD, "5 appels REST"),
        ("24 / 14", "apprenants / cours", BLUE, "MongoDB ou JSON"),
        ("0", "erreur de test", GREEN, "protocole nominal"),
    ]
    for i, (value, label, accent, sub) in enumerate(stats):
        stat(s, 0.65 + i * 3.08, 1.9, 2.88, 1.45, value, label, accent, sub)
    table(
        s,
        0.65,
        3.65,
        12.05,
        2.3,
        ["Test", "Résultat", "Preuve"],
        [
            ("Handshake MCP", "OK", "client Python, transport SSE"),
            ("Découverte", "6 outils", "list_tools"),
            ("Parcours L001", "3 étapes, 80 h", "VIZ220, STAT210, DATA350"),
            ("Quiz PY101", "3 questions", "QUIZ-… généré"),
        ],
        [4.2, 3.2, 4.65],
        9.5,
    )
    txt(s, 0.65, 6.15, 12.05, 0.35, "Le JSON final, le playground et le dashboard sont livrés avec le projet.",
        10.5, MUTED)
    footer(s, 8, total)
    notes(
        s,
        "Les tests couvrent le handshake, la découverte, le parcours et le quiz. Les six outils sont exposés "
        "et le client MCP les voit. La latence médiane est faible parce que tout est local ; en production, "
        "il faudra ajouter le réseau, le modèle et l'authentification.",
    )

    # 9 — sécurité
    s = blank(prs)
    header(s, "08 · Cadre de confiance", "Sécurité, limites et bonnes pratiques", "J33")
    rect(s, 0.65, 1.95, 5.85, 4.5, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 2.15, 5.2, 0.35, "CE QUI EST DÉJÀ PROTÉGÉ", 9, GREEN, True, char_spacing=1.5)
    paragraphs(
        s,
        0.95,
        2.6,
        5.15,
        3.5,
        [
            ("Données synthétiques : ", "aucun apprenant réel."),
            ("Bind localhost : ", "le serveur n'est pas exposé par défaut."),
            ("Outils bornés : ", "lecture et calcul, pas d'action irréversible."),
            ("Traçabilité : ", "outil, arguments, latence, résultat."),
        ],
        10.5,
        space_after=8,
    )
    rect(s, 6.8, 1.95, 5.9, 4.5, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 7.1, 2.15, 5.2, 0.35, "À RENFORCER EN PRODUCTION", 9, GOLD, True, char_spacing=1.5)
    paragraphs(
        s,
        7.1,
        2.6,
        5.2,
        3.5,
        [
            ("Authentification : ", "OAuth, TLS, allowlist."),
            ("Données réelles : ", "minimisation, RGPD, consentement."),
            ("Coût : ", "quotas, cache, timeout."),
            ("Qualité : ", "évaluation du LLM sur un jeu de questions."),
        ],
        10.5,
        space_after=8,
    )
    footer(s, 9, total)
    notes(
        s,
        "Le projet est sûr par construction : données synthétiques, serveur local, outils en lecture. "
        "Pour passer en production, il faudrait ajouter l'authentification, le chiffrement, la gestion des "
        "données personnelles et une évaluation systématique des réponses du modèle.",
    )

    # 10 — conclusion
    s = blank(prs)
    header(s, "09 · Conclusion", "MCP outille l'agent ; A2A fera collaborer les agents", "J33")
    rect(s, 0.65, 1.95, 12.05, 1.5, NAVY, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 2.2, 11.4, 0.45, "Un serveur, six outils, un agent qui les découvre.", 22, WHITE, True, line_spacing=0.95)
    txt(s, 0.95, 2.75, 11.4, 0.4, "Le contrat MCP remplace les intégrations spécifiques par une interface standard.",
        11, GOLD)
    three = [
        ("Découvrir", "list_tools expose les capacités du serveur.", TEAL),
        ("Choisir", "L'agent sélectionne l'outil et les arguments.", GOLD),
        ("Prouver", "Le playground et le dashboard montrent la trace.", BLUE),
    ]
    for i, (title, body, accent) in enumerate(three):
        card(s, 0.65 + i * 4.08, 3.8, 3.87, 1.65, title, body, accent, body_size=10.5)
    txt(s, 0.65, 5.9, 12.05, 0.4, "Prochaine étape · Jour 34 : trois agents spécialisés, des AgentCards et un orchestrateur A2A.",
        11.5, MUTED)
    footer(s, 10, total)
    notes(
        s,
        "En conclusion, MCP standardise l'accès aux outils. Le serveur publie, l'agent découvre et choisit, "
        "le playground prouve. Le jour 34 ajoute la collaboration entre agents avec A2A. Les deux briques "
        "sont complémentaires.",
    )

    # 11 — merci
    s = blank(prs)
    bg(s, NAVY)
    rect(s, 9.6, -1.2, 5.0, 5.0, RGBColor(0x12, 0x3A, 0x60), shape=MSO_SHAPE.OVAL)
    rect(s, 10.2, 4.4, 3.6, 3.6, RGBColor(0x0F, 0x31, 0x55), shape=MSO_SHAPE.OVAL)
    image(s, ASSETS / "logo.png", 0.7, 0.6, w=3.4)
    txt(s, 0.75, 2.6, 8.6, 1.2, "Merci.", 44, WHITE, True)
    txt(s, 0.78, 3.75, 8.4, 0.8, "Questions, démonstration et prochaines étapes.", 17, GOLD)
    txt(s, 0.78, 4.7, 8.4, 0.4, "localhost:8011 · serveur MCP :8000 · dépôt GitHub", 11, RGBColor(0xC9, 0xD8, 0xE8))
    txt(s, 0.78, 5.2, 8.4, 0.4, "Documentation · JSON · vidéo · dashboard", 10, RGBColor(0x9F, 0xB8, 0xD0))
    txt(s, 0.78, 6.55, 8.4, 0.3, "EduAgentic · J33 · 11 novembre 2026", 9, RGBColor(0x9F, 0xB8, 0xD0))
    notes(s, "Merci de votre attention. Nous pouvons maintenant passer à la démonstration du playground ou répondre aux questions.")

    path = DECK_DIR / "J33_MCP_Presentation.pptx"
    prs.save(path)
    return path


def add_j34() -> Path:
    prs = new_deck()
    total = 11
    cover(
        prs,
        "Jour 34 · Mini-projet · Correction finale",
        "A2A en EdTech :\nfaire collaborer des agents spécialisés",
        "AgentCards, découverte, délégation JSON-RPC et correlation_id",
        "Kamal El Afoui · Centre des Très Petites Entreprises Solidaires / DBA Technology · 11 novembre 2026",
        ["3 agents", "AgentCard", "correlation_id"],
    )
    notes(
        prs.slides[-1],
        "Bonjour. Cette présentation couvre le jour 34 : faire collaborer plusieurs agents spécialisés avec "
        "le protocole A2A. Nous allons voir les AgentCards, la découverte, la délégation et la traçabilité.",
    )

    # 2 — pourquoi
    s = blank(prs)
    header(s, "01 · Le constat", "Un agent ne possède pas toutes les compétences", "J34")
    pillars = [
        ("AgentCard", "Chaque agent publie son identité, ses compétences et son endpoint.", TEAL, "🪪"),
        ("Discovery", "L'orchestrateur découvre les agents disponibles sur le réseau.", BLUE, "🔎"),
        ("Delegation", "Une tâche est confiée au spécialiste, avec un correlation_id.", GOLD, "📨"),
    ]
    for i, (title, body, accent, icon) in enumerate(pillars):
        card(s, 0.65 + i * 4.08, 2.0, 3.87, 2.35, title, body, accent, icon, body_size=11.5)
    rect(s, 0.65, 4.75, 12.05, 1.25, NAVY, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 4.95, 11.4, 0.4, "A2A standardise la collaboration entre agents hétérogènes.", 17, WHITE, True)
    txt(s, 0.95, 5.38, 11.4, 0.3, "Découvrir · collaborer · déléguer · tracer, en toute sécurité.", 11, GOLD)
    footer(s, 2, total)
    notes(
        s,
        "Un agent seul ne peut pas tout faire correctement. A2A repose sur trois piliers : la carte d'identité "
        "de chaque agent, la découverte automatique et la délégation traçable. C'est ce triptyque que nous "
        "allons illustrer.",
    )

    # 3 — agents
    s = blank(prs)
    header(s, "02 · Les agents", "Trois spécialistes, un orchestrateur", "J34")
    agents = [
        ("Agent Tuteur", "Cours, ressources, parcours et prérequis.", "8101", TEAL, "🧑‍🏫", "search_courses · recommend_learning_path"),
        ("Agent Évaluation", "Quiz formatif, correction et feedback.", "8102", GOLD, "📝", "generate_quiz · grade_quiz"),
        ("Agent Orientation", "Écart de compétences et trajectoire métier.", "8103", BLUE, "🧭", "skill_gap · career_path"),
    ]
    for i, (name, desc, port, accent, icon, skills) in enumerate(agents):
        x = 0.65 + i * 4.08
        card(s, x, 2.0, 3.87, 2.85, name, desc, accent, icon, body_size=10.5)
        pill(s, x + 0.24, 4.22, 0.85, 0.28, f"port {port}", accent, WHITE, 8)
        txt(s, x + 0.24, 4.6, 3.4, 0.2, skills, 7.2, MUTED)
    rect(s, 0.65, 5.25, 12.05, 0.85, NAVY, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 5.42, 11.4, 0.5, "Orchestrateur : découvre les cartes, sélectionne, délègue en parallèle et agrège.",
        14, WHITE, True)
    footer(s, 3, total)
    notes(
        s,
        "Trois agents spécialisés : le Tuteur pour les cours et le parcours, l'Évaluation pour les quiz, "
        "l'Orientation pour les compétences et le métier. L'orchestrateur, lui, ne produit pas la réponse : "
        "il découvre les cartes, choisit les agents et agrège leurs résultats.",
    )

    # 4 — architecture
    s = blank(prs)
    header(s, "03 · Architecture", "Découvrir, déléguer, agréger", "J34")
    image(s, ASSETS / "architecture_a2a.png", 0.55, 1.55, w=9.4)
    rect(s, 10.2, 1.8, 2.55, 4.85, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 10.42, 2.0, 2.05, 0.3, "LE FLUX", 9, GOLD, True, char_spacing=2)
    steps = [("1", "Discovery"), ("2", "Sélection"), ("3", "Délégation"), ("4", "Agrégation")]
    yy = 2.4
    for num, label in steps:
        pill(s, 10.42, yy, 0.4, 0.4, num, NAVY, WHITE, 10)
        txt(s, 10.93, yy + 0.05, 1.65, 0.3, label, 10.5, NAVY, True)
        yy += 0.85
    txt(s, 10.42, 6.0, 2.0, 0.45, "Un correlation_id pour chaque demande.", 8.5, TEAL, True)
    footer(s, 4, total)
    notes(
        s,
        "L'architecture est volontairement symétrique : un orchestrateur au centre, trois agents autour, "
        "un dashboard à droite. Les flèches en pointillé représentent la découverte des cartes ; les flèches "
        "pleines représentent la délégation effective.",
    )

    # 5 — AgentCard
    s = blank(prs)
    header(s, "04 · AgentCard", "La carte d'identité que tout agent publie", "J34")
    code(
        s,
        0.65,
        1.85,
        7.3,
        4.7,
        """{
  "name": "Agent Tuteur",
  "url": "http://127.0.0.1:8101/",
  "version": "1.0.0",
  "protocolVersion": "0.3.0",
  "preferredTransport": "JSONRPC",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "recommend_learning_path",
      "name": "Parcours personnalisé",
      "tags": ["parcours", "prérequis"]
    }
  ]
}""",
        9.2,
        "json",
    )
    rect(s, 8.3, 1.85, 4.4, 4.7, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 8.55, 2.05, 3.9, 0.3, "CE QU'ELLE DÉCRIT", 9, GOLD, True, char_spacing=2)
    paragraphs(
        s,
        8.55,
        2.5,
        3.85,
        3.6,
        [
            ("Identité : ", "nom, type, version, organisation."),
            ("Compétences : ", "skills, tags, exemples."),
            ("Endpoint : ", "URL de délégation JSON-RPC."),
            ("Conditions : ", "usages autorisés, limites."),
            ("Capacités : ", "streaming, notifications, historique."),
        ],
        10,
        space_after=7,
    )
    footer(s, 5, total)
    notes(
        s,
        "L'AgentCard est le point d'entrée de toute collaboration. Elle publie le nom, l'endpoint, les "
        "compétences et les conditions d'utilisation. Sans carte, les autres agents ne savent ni ce que "
        "l'agent sait faire, ni comment le joindre.",
    )

    # 6 — protocole
    s = blank(prs)
    header(s, "05 · Protocole", "JSON-RPC 2.0 : message/send et tasks/get", "J34")
    steps = [
        ("1", "Message", "role, parts, contextId"),
        ("2", "Metadata", "correlation_id, learner_id"),
        ("3", "Task", "id, status, artifacts"),
        ("4", "Trace", "logs horodatés"),
    ]
    for i, (num, title, sub) in enumerate(steps):
        x = 0.65 + i * 3.08
        rect(s, x, 1.9, 2.88, 1.05, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        pill(s, x + 0.15, 2.02, 0.36, 0.36, num, GOLD, NAVY, 9)
        txt(s, x + 0.62, 2.0, 2.05, 0.3, title, 11, NAVY, True)
        txt(s, x + 0.62, 2.3, 2.05, 0.3, sub, 8, MUTED)
    code(
        s,
        0.65,
        3.3,
        12.05,
        3.2,
        """{
  "jsonrpc": "2.0",
  "id": "req-7f3a",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "Construis mon parcours Data Analyst"}],
      "contextId": "A2A-261111-120000-AB12"
    },
    "metadata": {
      "correlation_id": "A2A-261111-120000-AB12",
      "learner_id": "L001",
      "target_skill": "data-analysis"
    }
  }
}""",
        9.5,
        "json",
    )
    footer(s, 6, total)
    notes(
        s,
        "Le protocole repose sur JSON-RPC 2.0. Un message contient les parts textuelles, un contextId et des "
        "metadata. La réponse est une Task avec un statut et des artifacts. Le correlation_id relie la demande "
        "à toutes les délégations.",
    )

    # 7 — workflow
    s = blank(prs)
    header(s, "06 · Langflow", "Le workflow A2A : découvrir, déléguer, agréger", "J34")
    image(s, ASSETS / "workflow_a2a.png", 0.55, 1.55, w=9.55)
    rect(s, 10.35, 1.8, 2.4, 4.75, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 10.55, 2.0, 2.0, 0.3, "POINTS CLÉS", 8.5, GOLD, True, char_spacing=1.5)
    paragraphs(
        s,
        10.55,
        2.45,
        2.0,
        3.8,
        [
            ("3 agents ", "indépendants."),
            ("3 délégations ", "parallèles."),
            ("1 correlation_id ", "par demande."),
            ("1 réponse ", "agrégée."),
        ],
        9,
        space_after=8,
    )
    footer(s, 7, total)
    notes(
        s,
        "Le workflow Langflow reprend la même logique : un Chat Input, une découverte des cartes, un "
        "orchestrateur, trois agents et un Chat Output. Le JSON final est fourni avec le projet et documenté "
        "dans la documentation J34.",
    )

    # 8 — démo
    s = blank(prs)
    header(s, "07 · Démonstration", "Le dashboard montre la timeline et les artifacts", "J34")
    if (SHOTS / "a2a_result2.png").exists():
        image(s, SHOTS / "a2a_result2.png", 0.45, 1.55, w=8.0)
    rect(s, 8.75, 1.7, 4.05, 4.95, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 9.0, 1.9, 3.5, 0.3, "RÉSULTAT", 8.5, GOLD, True, char_spacing=1.5)
    paragraphs(
        s,
        9.0,
        2.35,
        3.55,
        4.0,
        [
            ("Découverte : ", "3 agents en ligne."),
            ("Délégation : ", "3 appels en parallèle."),
            ("Latence : ", "quelques dizaines de ms."),
            ("Réponse : ", "parcours + ressources + quiz."),
            ("Trace : ", "correlation_id et logs."),
        ],
        10,
        space_after=7,
    )
    footer(s, 8, total)
    notes(
        s,
        "Dans le dashboard, on choisit un apprenant et un objectif, puis on lance l'orchestration. La timeline "
        "montre les trois agents, leur statut et leur latence. La réponse consolidée contient le parcours, "
        "les ressources et le quiz.",
    )

    # 9 — correlation
    s = blank(prs)
    header(s, "08 · Traçabilité", "Un correlation_id pour relier chaque échange", "J34")
    table(
        s,
        0.65,
        1.9,
        12.05,
        2.2,
        ["Heure", "Source → cible", "Statut", "Latence"],
        [
            ("12:00:01", "orchestrateur → agent-orientation", "completed", "23 ms"),
            ("12:00:01", "orchestrateur → agent-tuteur", "completed", "27 ms"),
            ("12:00:01", "orchestrateur → agent-evaluation", "completed", "26 ms"),
        ],
        [2.4, 6.4, 1.6, 1.65],
        10.5,
    )
    rect(s, 0.65, 4.4, 12.05, 1.6, RGBColor(0xFF, 0xF8, 0xE1), radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 4.6, 11.4, 0.35, "A2A-261111-120000-AB12", 20, NAVY, True)
    txt(s, 0.95, 5.05, 11.4, 0.7, "Sans correlation_id, il est impossible de relier plusieurs échanges appartenant à la même tâche.",
        11, MUTED)
    footer(s, 9, total)
    notes(
        s,
        "Le correlation_id est l'élément central de la traçabilité. Il permet de retracer le parcours d'une "
        "demande, d'identifier un agent lent ou en erreur et de comparer les performances. C'est indispensable "
        "pour expliquer une réponse composée de plusieurs agents.",
    )

    # 10 — résultats
    s = blank(prs)
    header(s, "09 · Résultats", "Trois agents, trois délégations, une réponse", "J34")
    stats = [
        ("3 / 3", "agents découverts", TEAL, "GET /discover"),
        ("3 / 3", "délégations completed", GOLD, "timeline"),
        (f"{A2A_MS} ms", "orchestration", BLUE, "test HTTP"),
        ("100 %", "artifacts présents", GREEN, "timeline + logs"),
    ]
    for i, (value, label, accent, sub) in enumerate(stats):
        stat(s, 0.65 + i * 3.08, 1.9, 2.88, 1.45, value, label, accent, sub)
    table(
        s,
        0.65,
        3.65,
        12.05,
        2.15,
        ["Point", "Constat", "Limite"],
        [
            ("Découverte", "3 cartes accessibles", "Pas de signature des cartes"),
            ("Délégation", "3 appels parallèles", "Pas de retry automatique"),
            ("Traçabilité", "logs corrélés", "Pas de streaming"),
        ],
        [3.0, 4.6, 4.45],
        10,
    )
    footer(s, 10, total)
    notes(
        s,
        "Les résultats sont conformes : les trois agents sont découverts, les trois délégations aboutissent "
        "et les artifacts sont présents. Les limites sont connues : pas de signature de carte, pas de retry, "
        "pas de streaming. Ce sont les prochaines étapes.",
    )

    # 11 — conclusion
    s = blank(prs)
    bg(s, NAVY)
    rect(s, 9.6, -1.2, 5.0, 5.0, RGBColor(0x12, 0x3A, 0x60), shape=MSO_SHAPE.OVAL)
    rect(s, 10.2, 4.4, 3.6, 3.6, RGBColor(0x0F, 0x31, 0x55), shape=MSO_SHAPE.OVAL)
    image(s, ASSETS / "logo.png", 0.7, 0.6, w=3.4)
    txt(s, 0.75, 2.5, 8.6, 1.0, "Collaborer,\npas tout faire.", 34, WHITE, True, line_spacing=0.95)
    txt(s, 0.78, 3.85, 8.4, 0.8, "A2A transforme trois agents spécialisés en une équipe traçable.", 15, GOLD)
    txt(s, 0.78, 4.9, 8.4, 0.35, "3 AgentCards · 1 orchestrateur · 1 correlation_id", 11, RGBColor(0xC9, 0xD8, 0xE8))
    txt(s, 0.78, 6.55, 8.4, 0.3, "EduAgentic · J34 · 11 novembre 2026", 9, RGBColor(0x9F, 0xB8, 0xD0))
    notes(s, "En conclusion, A2A permet à des agents spécialisés de collaborer sans se connaître. Le correlation_id rend cette collaboration vérifiable. Merci.")

    path = DECK_DIR / "J34_A2A_Presentation.pptx"
    prs.save(path)
    return path


def add_final() -> Path:
    prs = new_deck()
    total = 12
    cover(
        prs,
        "Synthèse · Jours 33 & 34 · Correction finale",
        "Agentic AI in EdTech :\nMCP & A2A",
        "Deux protocoles, une plateforme d'apprentissage augmentée",
        "Kamal El Afoui · Centre des Très Petites Entreprises Solidaires / DBA Technology · 11 novembre 2026",
        ["MCP", "A2A", "Dashboard 8011"],
    )
    notes(
        prs.slides[-1],
        "Cette présentation synthétise les deux mini-projets. Le jour 33 outille un agent avec MCP. Le jour 34 "
        "fait collaborer trois agents avec A2A. Le dashboard 8011 relie les deux démonstrations.",
    )

    # 2 — comparaison
    s = blank(prs)
    header(s, "01 · Vue d'ensemble", "Deux protocoles, une même plateforme", "")
    rect(s, 0.65, 1.9, 5.85, 4.5, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 0.95, 2.1, 5.2, 0.35, "MCP · JOUR 33", 10, GOLD, True, char_spacing=2)
    txt(s, 0.95, 2.5, 5.2, 0.5, "Outiller l'agent", 20, NAVY, True)
    paragraphs(
        s,
        0.95,
        3.1,
        5.15,
        3.0,
        [
            ("Serveur : ", "FastMCP, 6 outils, SSE."),
            ("Workflow : ", "Chat Input → Agent → MCP Tools."),
            ("Preuve : ", "playground + trace des appels."),
            ("Question : ", "comment accéder aux outils ?"),
        ],
        10.5,
        space_after=7,
    )
    rect(s, 6.8, 1.9, 5.9, 4.5, NAVY, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 7.1, 2.1, 5.2, 0.35, "A2A · JOUR 34", 10, TEAL, True, char_spacing=2)
    txt(s, 7.1, 2.5, 5.2, 0.5, "Faire collaborer", 20, WHITE, True)
    paragraphs(
        s,
        7.1,
        3.1,
        5.2,
        3.0,
        [
            ("Agents : ", "Tuteur, Évaluation, Orientation."),
            ("Workflow : ", "découverte → délégation → agrégation."),
            ("Preuve : ", "timeline + correlation_id."),
            ("Question : ", "comment répartir une tâche ?"),
        ],
        10.5,
        WHITE,
        TEAL,
        space_after=7,
        lead_color=WHITE,
    )
    footer(s, 2, total)
    notes(
        s,
        "MCP et A2A répondent à deux questions différentes. MCP outille un agent : il expose des fonctions. "
        "A2A fait collaborer des agents : il expose des compétences. Les deux protocoles se complètent dans "
        "une même plateforme.",
    )

    # 3 — J33
    s = blank(prs)
    header(s, "02 · Jour 33", "MCP : six outils, un agent, une trace", "J33")
    if (ASSETS / "workflow_mcp.png").exists():
        image(s, ASSETS / "workflow_mcp.png", 0.55, 1.6, w=8.9)
    stats = [("6", "outils"), (f"{MCP_MS} ms", "latence"), ("100 %", "synthétique")]
    for i, (value, label) in enumerate(stats):
        stat(s, 9.85, 1.7 + i * 1.55, 2.9, 1.25, value, label, [TEAL, GOLD, BLUE][i], value_size=22)
    txt(s, 9.85, 6.35, 2.9, 0.3, "Workflow JSON livré", 9, MUTED)
    footer(s, 3, total)
    notes(
        s,
        "Le jour 33, c'est un serveur MCP avec six outils et un workflow Langflow. L'agent découvre les outils, "
        "les appelle et le playground montre la trace. Le JSON final et la vidéo sont livrés.",
    )

    # 4 — J34
    s = blank(prs)
    header(s, "03 · Jour 34", "A2A : trois agents, un orchestrateur, un identifiant", "J34")
    if (ASSETS / "workflow_a2a.png").exists():
        image(s, ASSETS / "workflow_a2a.png", 0.55, 1.6, w=8.9)
    stats = [("3", "agents"), ("3", "délégations"), ("1", "correlation_id")]
    for i, (value, label) in enumerate(stats):
        stat(s, 9.85, 1.7 + i * 1.55, 2.9, 1.25, value, label, [TEAL, GOLD, BLUE][i], value_size=22)
    txt(s, 9.85, 6.35, 2.9, 0.3, "Timeline + logs", 9, MUTED)
    footer(s, 4, total)
    notes(
        s,
        "Le jour 34, c'est un orchestrateur et trois agents. L'orchestrateur découvre les cartes, délègue en "
        "parallèle et agrège. Chaque demande porte un correlation_id, visible dans la timeline et les logs.",
    )

    # 5 — dashboard
    s = blank(prs)
    header(s, "04 · Dashboard", "localhost:8011 : le point d'observation", "")
    if (SHOTS / "home.png").exists():
        image(s, SHOTS / "home.png", 0.45, 1.55, w=8.1)
    rect(s, 8.85, 1.7, 3.95, 4.9, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 9.1, 1.9, 3.4, 0.3, "DANS LE MENU", 8.5, GOLD, True, char_spacing=1.5)
    paragraphs(
        s,
        9.1,
        2.35,
        3.45,
        3.95,
        [
            ("Vue d'ensemble : ", "KPI et activité récente."),
            ("MCP Playground : ", "formulaire + trace."),
            ("A2A Orchestration : ", "timeline et artifacts."),
            ("Statistiques : ", "6 graphiques filtrables."),
            ("Documentation : ", "livrables téléchargeables."),
        ],
        9.5,
        space_after=6,
    )
    footer(s, 5, total)
    notes(
        s,
        "Le dashboard est le point d'observation commun. Le menu donne accès à la vue d'ensemble, au playground "
        "MCP, à l'orchestration A2A, aux statistiques et aux livrables. Toutes les pages sont connectées aux "
        "mêmes données et aux mêmes services.",
    )

    # 6 — stats
    s = blank(prs)
    header(s, "05 · Statistiques", "Les chiffres du jeu de données EdTech", "")
    if (SHOTS / "stats_fixed.png").exists():
        image(s, SHOTS / "stats_fixed.png", 0.45, 1.55, w=8.15)
    rect(s, 8.9, 1.7, 3.9, 4.9, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(s, 9.15, 1.9, 3.4, 0.3, "KPI CLÉS", 8.5, GOLD, True, char_spacing=1.5)
    kpis = [
        ("24", "apprenants"),
        ("14", "cours"),
        ("74,4", "score moyen"),
        ("64,3 %", "réussite quiz"),
        ("92,9 %", "succès A2A"),
    ]
    yy = 2.4
    for value, label in kpis:
        txt(s, 9.15, yy, 1.1, 0.35, value, 18, NAVY, True)
        txt(s, 10.3, yy + 0.08, 2.2, 0.25, label, 9, MUTED)
        yy += 0.7
    footer(s, 6, total)
    notes(
        s,
        "Les statistiques sont calculées à partir des données brutes : 24 apprenants, 14 cours, 168 tentatives. "
        "Le score moyen est de 74,4 et la réussite de 64,3 %. Côté A2A, 92,9 % des délégations du jeu de test "
        "sont complétées.",
    )

    # 7 — résultats
    s = blank(prs)
    header(s, "06 · Résultats", "Ce que les deux mini-projets démontrent", "")
    stats = [
        ("6", "outils MCP", TEAL, "découverts et testés"),
        ("3", "agents A2A", GOLD, "découverts et délégés"),
        (f"{A2A_MS} ms", "orchestration", BLUE, "test local"),
        ("0", "exception dashboard", GREEN, "6 pages"),
    ]
    for i, (value, label, accent, sub) in enumerate(stats):
        stat(s, 0.65 + i * 3.08, 1.95, 2.88, 1.5, value, label, accent, sub)
    table(
        s,
        0.65,
        3.8,
        12.05,
        2.0,
        ["Preuve", "MCP", "A2A"],
        [
            ("Découverte", "6 outils listés", "3 AgentCards"),
            ("Exécution", "5 appels testés", "3 délégations completed"),
            ("Traçabilité", "trace outil + latence", "correlation_id + logs"),
        ],
        [3.0, 4.5, 4.55],
        10,
    )
    footer(s, 7, total)
    notes(
        s,
        "Les résultats sont reproductibles : six outils, trois agents, zéro exception sur le dashboard. "
        "La latence A2A est de l'ordre de quelques dizaines à quelques centaines de millisecondes en local. "
        "Les preuves sont dans les traces et les logs.",
    )

    # 8 — traçabilité
    s = blank(prs)
    header(s, "07 · Confiance", "Traçabilité, sécurité, limites", "")
    cols = [
        ("TRACER", ["Outil + arguments + latence", "correlation_id par demande", "Logs horodatés", "Artifacts inspectables"], TEAL),
        ("PROTÉGER", ["Données 100 % synthétiques", "Serveur bind localhost", "Outils en lecture", "Pas de secret dans le dépôt"], BLUE),
        ("AMÉLIORER", ["Authentification OAuth", "Retry et timeout par agent", "Évaluation du LLM", "Streaming SSE"], GOLD),
    ]
    for i, (title, items, accent) in enumerate(cols):
        x = 0.65 + i * 4.08
        rect(s, x, 1.95, 3.87, 4.4, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        txt(s, x + 0.25, 2.15, 3.3, 0.3, title, 9, accent, True, char_spacing=2)
        paragraphs(s, x + 0.25, 2.65, 3.35, 3.4, [(item, "") for item in items], 10, space_after=10)
    footer(s, 8, total)
    notes(
        s,
        "La confiance repose sur trois axes. Tracer : chaque appel est horodaté et corrélé. Protéger : les "
        "données sont synthétiques et le serveur reste local. Améliorer : authentification, retry, évaluation "
        "et streaming sont les prochaines étapes.",
    )

    # 9 — livrables
    s = blank(prs)
    header(s, "08 · Livrables", "Tout est documenté, versionné et reproductible", "")
    table(
        s,
        0.65,
        1.9,
        12.05,
        3.8,
        ["Livrable", "Contenu", "Format"],
        [
            ("Code", "MCP, A2A, dashboard, scripts", "Python"),
            ("JSON", "Workflows MCP et A2A", "JSON"),
            ("Documentation", "J33, J34, synthèse", "DOCX / PDF"),
            ("Présentations", "J33, J34, finale", "PPTX / PDF"),
            ("Vidéos", "Workflow + playground, finale", "MP4"),
            ("Dashboard", "localhost:8011", "Streamlit"),
            ("Dépôt", "GitHub + archive", "Git / ZIP"),
        ],
        [3.0, 6.6, 2.45],
        9.8,
    )
    txt(s, 0.65, 6.0, 12.05, 0.4, "Chaque livrable est généré à partir du même jeu de données et des mêmes workflows.",
        10.5, MUTED)
    footer(s, 9, total)
    notes(
        s,
        "Les livrables couvrent le code, les JSON, les documents, les présentations, les vidéos et le dashboard. "
        "Tout est versionné et reproductible. Le zip final contient l'ensemble, et le dépôt GitHub permet de "
        "suivre l'historique.",
    )

    # 10 — démo
    s = blank(prs)
    header(s, "09 · Démonstration", "Quatre étapes pour rejouer la démo", "")
    steps = [
        ("1", "Lancer les services", "python a2a/run_all.py --with-dashboard", TEAL),
        ("2", "Ouvrir le dashboard", "http://localhost:8011", BLUE),
        ("3", "Tester MCP", "Parcours, quiz, statistiques", GOLD),
        ("4", "Tester A2A", "Orchestration + timeline", GREEN),
    ]
    for i, (num, title, sub, accent) in enumerate(steps):
        x = 0.65 + (i % 2) * 6.1
        y = 1.95 + (i // 2) * 2.15
        rect(s, x, y, 5.85, 1.8, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        pill(s, x + 0.2, y + 0.2, 0.45, 0.45, num, accent, WHITE, 11)
        txt(s, x + 0.85, y + 0.2, 4.7, 0.35, title, 14, NAVY, True)
        txt(s, x + 0.85, y + 0.72, 4.7, 0.6, sub, 10.5, MUTED)
    footer(s, 10, total)
    notes(
        s,
        "Pour rejouer la démonstration, il suffit de lancer les services, d'ouvrir le dashboard, puis de tester "
        "le playground MCP et l'orchestration A2A. Les commandes sont dans le README et dans le mode d'emploi "
        "des documentations.",
    )

    # 11 — conclusion
    s = blank(prs)
    header(s, "10 · Conclusion", "Trois messages à retenir", "")
    messages = [
        ("01", "MCP outille", "Un serveur publie ses outils ; l'agent les découvre et les appelle.", TEAL),
        ("02", "A2A coordonne", "Des agents spécialisés se découvrent, se délèguent et s'agrègent.", GOLD),
        ("03", "Le dashboard prouve", "Traces, KPI et vidéos rendent la démonstration vérifiable.", BLUE),
    ]
    for i, (num, title, body, accent) in enumerate(messages):
        rect(s, 0.65 + i * 4.08, 2.0, 3.87, 3.35, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        txt(s, 0.9 + i * 4.08, 2.2, 1.0, 0.5, num, 22, accent, True, TITLE_FONT)
        txt(s, 0.9 + i * 4.08, 2.85, 3.35, 0.45, title, 15, NAVY, True)
        txt(s, 0.9 + i * 4.08, 3.4, 3.3, 1.5, body, 10.5, MUTED, line_spacing=1.1)
    txt(s, 0.65, 5.9, 12.05, 0.4, "Deux mini-projets autonomes, une plateforme cohérente, une démonstration reproductible.",
        11.5, MUTED)
    footer(s, 11, total)
    notes(
        s,
        "Trois messages : MCP outille l'agent, A2A coordonne les agents, le dashboard prouve le fonctionnement. "
        "Les deux mini-projets sont autonomes mais forment une plateforme cohérente.",
    )

    # 12 — merci
    s = blank(prs)
    bg(s, NAVY)
    rect(s, 9.6, -1.2, 5.0, 5.0, RGBColor(0x12, 0x3A, 0x60), shape=MSO_SHAPE.OVAL)
    rect(s, 10.2, 4.4, 3.6, 3.6, RGBColor(0x0F, 0x31, 0x55), shape=MSO_SHAPE.OVAL)
    image(s, ASSETS / "logo.png", 0.7, 0.6, w=3.4)
    txt(s, 0.75, 2.6, 8.6, 1.2, "Merci.", 44, WHITE, True)
    txt(s, 0.78, 3.8, 8.4, 0.8, "Place à la démonstration et aux questions.", 17, GOLD)
    txt(s, 0.78, 4.95, 8.4, 0.35, "localhost:8011 · MCP :8000 · A2A :8001", 11, RGBColor(0xC9, 0xD8, 0xE8))
    txt(s, 0.78, 6.55, 8.4, 0.3, "EduAgentic · J33/J34 · 11 novembre 2026", 9, RGBColor(0x9F, 0xB8, 0xD0))
    notes(s, "Merci de votre attention. Nous pouvons maintenant ouvrir le dashboard et dérouler la démonstration.")

    path = DECK_DIR / "Presentation_Finale_J33_J34.pptx"
    prs.save(path)
    return path


def export_pdf(paths: list[Path]) -> None:
    import win32com.client as win32

    app = win32.DispatchEx("PowerPoint.Application")
    try:
        app.Visible = True
    except Exception:
        pass
    app.DisplayAlerts = 0
    try:
        for path in paths:
            prs = app.Presentations.Open(str(path), WithWindow=False)
            try:
                pdf = path.with_suffix(".pdf")
                prs.SaveAs(str(pdf), 32)  # ppSaveAsPDF
                print("  PDF :", pdf.name, f"{pdf.stat().st_size/1024:.0f} Ko")
            finally:
                prs.Close()
    finally:
        app.Quit()


def main() -> None:
    print("Construction des présentations…")
    paths = [add_j33(), add_j34(), add_final()]
    for path in paths:
        print("  PPTX :", path.name, f"{path.stat().st_size/1024:.0f} Ko")
    print("Export PDF…")
    export_pdf(paths)
    print("Présentations terminées.")


if __name__ == "__main__":
    main()

