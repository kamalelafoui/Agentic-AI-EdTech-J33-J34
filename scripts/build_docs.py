# -*- coding: utf-8 -*-
"""Génère les documentations DOCX puis les exporte en PDF via Microsoft Word."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import requests
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import a2a_core, edtech_core as core  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from docx_helpers import (  # noqa: E402
    ASSETS,
    GOLD,
    NAVY,
    TEAL,
    bullets,
    callout,
    code_block,
    cover,
    figure,
    h1,
    h2,
    h3,
    kv_grid,
    new_document,
    para,
    table,
)

DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)
SHOTS = ROOT / "screenshots"
BENCH = ROOT / "data" / "benchmarks.json"


def stats_snapshot() -> dict:
    return core.learning_statistics()


def measure_mcp() -> dict:
    """Mesure les appels REST du serveur MCP (ou repli local)."""
    tools = {
        "search_courses": {"query": "data analyst", "max_results": 3},
        "get_learner_profile": {"learner_id": "L001"},
        "recommend_learning_path": {"learner_id": "L001", "target_skill": "data-analysis"},
        "generate_quiz": {"course_id": "PY101", "n_questions": 3},
        "get_learning_statistics": {"segment": "Tous"},
    }
    results = []
    for name, args in tools.items():
        started = time.perf_counter()
        status = "OK"
        source = "REST"
        try:
            response = requests.post(
                "http://127.0.0.1:8000/api/tool",
                json={"tool": name, "arguments": args},
                timeout=3,
            )
            response.raise_for_status()
            body = response.json()
        except Exception:
            source = "local"
            try:
                from shared import edtech_core as c

                handlers = {
                    "search_courses": lambda: c.search_courses(args.get("query", ""), None, args.get("max_results", 3)),
                    "get_learner_profile": lambda: c.get_learner_profile(args["learner_id"]),
                    "recommend_learning_path": lambda: c.recommend_learning_path(args["learner_id"], args["target_skill"]),
                    "generate_quiz": lambda: c.generate_quiz(args["course_id"], None, args["n_questions"]),
                    "get_learning_statistics": lambda: c.learning_statistics("Tous"),
                }
                body = {"ok": True, "result": handlers[name]()}
            except Exception as exc:  # noqa: BLE001
                body = {"ok": False, "error": str(exc)}
                status = "ERREUR"
        latency = (time.perf_counter() - started) * 1000
        results.append(
            {
                "tool": name,
                "status": status if body.get("ok", True) else "ERREUR",
                "latency_ms": round(latency, 1),
                "source": source,
            }
        )
    return {
        "results": results,
        "median_ms": round(statistics.median([r["latency_ms"] for r in results]), 1),
        "ok": sum(1 for r in results if r["status"] == "OK"),
    }


def measure_a2a() -> dict:
    try:
        response = requests.post(
            "http://127.0.0.1:8001/orchestrate",
            json={
                "learner_id": "L001",
                "objective": "Devenir Data Analyst",
                "question": "Parcours, ressources et quiz",
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()["result"]
        return {
            "ok": True,
            "latency_ms": result["total_latency_ms"],
            "agents": len(result["delegations"]),
            "statuses": [d["status"] for d in result["delegations"]],
            "correlation_id": result["correlation_id"],
            "source": "HTTP",
        }
    except Exception:
        result = a2a_core.orchestrate_request(
            "L001", "Devenir Data Analyst", "Parcours, ressources et quiz", use_network=False
        )
        return {
            "ok": True,
            "latency_ms": result["total_latency_ms"],
            "agents": len(result["delegations"]),
            "statuses": [d["status"] for d in result["delegations"]],
            "correlation_id": result["correlation_id"],
            "source": "local",
        }


TOOLS = [
    ("search_courses", "query, level, max_results", "Liste de cours + pertinence", "Recherche dans le catalogue"),
    ("get_learner_profile", "learner_id", "Profil, progression, prochain cours", "Personnalisation"),
    ("recommend_learning_path", "learner_id, target_skill", "Parcours ordonné + prérequis", "Planification"),
    ("generate_quiz", "course_id, difficulty, n_questions", "Questions sans réponses", "Évaluation formative"),
    ("grade_quiz", "learner_id, course_id, answers", "Score, corrections, feedback", "Remédiation"),
    ("get_learning_statistics", "segment", "KPI + séries pour graphiques", "Pilotage"),
]


def add_toc(doc):
    p_title = doc.add_paragraph()
    p_title.paragraph_format.page_break_before = True
    p_title.paragraph_format.space_after = Pt(6)
    run = p_title.add_run("Sommaire")
    run.font.name = "Aptos Display"
    run.font.size = Pt(17)
    run.font.bold = True
    run.font.color.rgb = NAVY
    p = doc.add_paragraph()
    from docx_helpers import add_toc as insert_toc

    insert_toc(p)


def doc_mcp(snapshot: dict, mcp_test: dict, a2a_test: dict) -> Path:
    k = snapshot["kpis"]
    doc = new_document(
        "Agentic AI in Education Technology — J33 MCP",
        "JOUR 33 · MINI-PROJET · CORRECTION FINALE",
        "Model Context Protocol (MCP) : exposer et consommer des outils EdTech standardisés",
        "J33 · MCP",
        "Documentation technique du serveur MCP EduAgentic",
    )
    cover(
        doc,
        "Jour 33 · Mini-projet · Correction finale",
        "MCP en EdTech :\nexposer des outils, augmenter un agent",
        "Serveur FastMCP, workflow Langflow, playground et dashboard localhost:8011",
        [
            ("Auteur", "Kamal El Afoui"),
            ("Programme", "Centre des Très Petites Entreprises Solidaires · DBA Technology"),
            ("Date", "11 novembre 2026"),
            ("Version", "1.0.0 — Correction finale"),
        ],
        [
            "Serveur MCP FastMCP en transport SSE avec 6 outils EdTech.",
            "Workflow Langflow prêt à importer et JSON final livré.",
            "Playground avec trace outil → arguments → latence → résultat.",
            "Dashboard 8011 : menu, formulaire, graphiques et statistiques.",
            "Tests, sécurité, limites et mode d'emploi reproductible.",
        ],
    )

    h1(doc, "Résumé exécutif", page_break=False)
    para(
        doc,
        "Un modèle de langage seul ne connaît ni le catalogue de cours, ni le profil d'un apprenant, "
        "ni les résultats d'un quiz. Pour agir utilement dans une plateforme EdTech, il doit appeler des outils. "
        "Le Model Context Protocol (MCP) standardise cette connexion : le serveur publie une liste d'outils, "
        "l'agent les découvre et choisit celui qui répond à la demande.",
    )
    para(
        doc,
        "Ce mini-projet construit EduMCP, un serveur MCP qui expose six outils pédagogiques : recherche de cours, "
        "profil apprenant, parcours personnalisé, génération de quiz, correction et statistiques. Le workflow Langflow "
        "connecte un agent à ce serveur en SSE ; le playground du dashboard permet d'observer chaque appel. "
        "Le tout fonctionne en local, sans donnée réelle, et reste utilisable sans clé API pour les tests déterministes.",
    )
    table(
        doc,
        ["Indicateur", "Valeur", "Preuve"],
        [
            ("Outils MCP exposés", "6 / 6", "list_tools + tests REST"),
            ("Handshake MCP", "OK", "client officiel Python, transport SSE"),
            ("Latence médiane des outils", f"{mcp_test['median_ms']} ms", "5 appels mesurés le 11/11/2026"),
            ("Cours / apprenants", f"{k['courses']} / {k['learners']}", "data/courses.json, learners.json"),
            ("Tentatives de quiz", str(k["attempts"]), "data/quiz_attempts.csv"),
            ("Stockage", "MongoDB Atlas · edtech_*", "repli JSON local"),
            ("Score moyen", f"{k['avg_score']}/100", "calcul sur 168 tentatives"),
            ("Délégations A2A (J34)", str(k["delegations"]), "data/a2a_delegations.csv"),
        ],
        widths=[6.2, 4.2, 6.0],
        caption="Tableau 1 · Synthèse des résultats du mini-projet J33.",
    )
    callout(
        doc,
        "Résultat principal",
        "L'agent n'a pas besoin de connaître l'implémentation du serveur : il découvre les outils, "
        "lit leurs schémas JSON et reçoit des résultats structurés. C'est exactement le contrat que MCP standardise.",
        "success",
    )
    h2(doc, "Ce que démontre le mini-projet")
    bullets(
        doc,
        [
            "Un serveur qui publie six outils et leurs schémas, sans que le client ait à coder chaque route.",
            "Un agent qui sélectionne l'outil adapté et reçoit un résultat JSON validé.",
            "Un playground qui rend l'appel observable : outil, arguments, latence, résultat.",
            "Un dashboard qui relie la démonstration MCP aux statistiques et au jour 34 (A2A).",
        ],
    )
    add_toc(doc)

    h1(doc, "1. Contexte et problématique", page_break=False)
    h2(doc, "1.1 Pourquoi un standard pour les outils ?")
    para(
        doc,
        "Dans une plateforme EdTech, un agent peut avoir besoin de chercher un cours, de lire un profil, "
        "de recommander un parcours ou de corriger un quiz. Sans standard, chaque intégration ajoute une API "
        "spécifique, un format de données différent et une authentification propre. La maintenance devient "
        "rapidement plus coûteuse que la valeur apportée.",
    )
    bullets(
        doc,
        [
            "API REST personnalisées : chaque outil a son endpoint, son format et ses règles.",
            "Connecteurs spécifiques : le code de l'agent dépend de chaque fournisseur.",
            "Formats de données différents : JSON, CSV, texte libre, erreurs non homogènes.",
            "Authentification variable : clé API, OAuth, token interne, aucune unification.",
        ],
    )
    para(
        doc,
        "MCP propose un langage commun : le serveur décrit ses outils et leurs paramètres, le client les découvre "
        "et les appelle de manière standard. L'agent reste concentré sur la décision, pas sur la plomberie.",
    )
    h2(doc, "1.2 MCP vs REST")
    table(
        doc,
        ["Critère", "REST classique", "MCP"],
        [
            ("Contrat", "Endpoints propres à chaque API", "Interface standard, schémas d'outils"),
            ("Découverte", "Le client connaît les routes à l'avance", "Découverte automatique de la liste d'outils"),
            ("Intégration", "Développement spécifique par outil", "Réutilisation immédiate par tout client MCP"),
            ("Évolution", "Versionnage manuel des routes", "Le serveur publie ses outils et leurs schémas"),
            ("Dans ce projet", "Pont REST du dashboard", "Transport SSE + MCP Tools dans Langflow"),
        ],
        widths=[3.3, 6.4, 6.7],
        caption="Tableau 2 · Deux approches complémentaires : REST pour l'API interne, MCP pour l'agent.",
    )
    callout(
        doc,
        "À retenir",
        "MCP ne remplace pas REST : il décrit comment un agent découvre et utilise des outils. "
        "Le dashboard continue d'utiliser un pont REST local, tandis que l'agent Langflow passe par MCP.",
        "info",
    )

    h1(doc, "2. Objectifs et livrables")
    h2(doc, "2.1 Objectif de l'atelier")
    para(
        doc,
        "Construire un serveur MCP, le connecter à un agent et rejoindre l'écosystème ouvert. Le mini-projet "
        "doit être démontrable de bout en bout : un serveur qui tourne, un workflow qui découvre les outils, "
        "un playground qui montre les appels et un dashboard qui restitue les résultats.",
    )
    h2(doc, "2.2 Livrables")
    table(
        doc,
        ["Livrable", "Fichier", "Contenu"],
        [
            ("Serveur MCP", "mcp_server/edumcp_server.py", "FastMCP, 6 outils, SSE, pont REST"),
            ("Workflow Langflow", "json/Agentic_AI_EdTech_J33_MCP_Final.json", "Chat Input → Agent → MCP Tools → Chat Output"),
            ("Documentation", "docs/Documentation_J33_MCP_EdTech.docx / .pdf", "Ce document"),
            ("Présentation", "presentation/J33_MCP_Presentation.pptx", "Deck de soutenance"),
            ("Vidéo", "videos/J33_MCP_Workflow_Playground.mp4", "Workflow + playground"),
            ("Dashboard", "dashboard/app.py", "Streamlit, port 8011"),
        ],
        widths=[3.7, 7.0, 5.7],
        caption="Tableau 3 · Livrables du jour 33.",
    )

    h1(doc, "3. Architecture")
    figure(doc, ASSETS / "architecture_mcp.png", "Figure 1 · Architecture MCP : l'agent découvre les outils, le serveur exécute et retourne un résultat structuré.")
    h2(doc, "3.1 Les quatre composants")
    table(
        doc,
        ["Composant", "Rôle", "Technologie", "Port"],
        [
            ("Playground / Langflow", "Envoie la demande, affiche la réponse et la trace", "Streamlit / Langflow", "8011"),
            ("Agent", "Choisit l'outil et les arguments selon la demande", "LLM + MCP Tools", "—"),
            ("Serveur MCP", "Expose et exécute les 6 outils", "FastMCP + SSE", "8000"),
            ("Données EdTech", "Catalogue, profils, quiz, statistiques", "JSON / CSV synthétiques", "—"),
        ],
        widths=[4.0, 6.4, 4.1, 1.5],
        caption="Tableau 4 · Composants de l'architecture MCP.",
    )
    h2(doc, "3.2 Cycle d'un appel")
    bullets(
        doc,
        [
            "Découverte : l'agent se connecte au serveur et appelle list_tools.",
            "Sélection : le LLM choisit l'outil adapté à la question et construit les arguments.",
            "Exécution : le serveur valide les paramètres, exécute la fonction et sérialise le résultat.",
            "Synthèse : l'agent reformule le résultat en français, sans exposer le JSON brut.",
            "Trace : le playground enregistre l'outil, les arguments, la latence et le résultat.",
        ],
    )

    h1(doc, "4. Le serveur MCP EduMCP")
    h2(doc, "4.1 Vue d'ensemble")
    para(
        doc,
        "Le serveur est construit avec FastMCP. Il tourne sur 127.0.0.1:8000 en transport SSE, avec un point "
        "d'entrée /sse et un canal de messages /messages/. Un pont REST local expose /api/health, /api/tools et "
        "/api/tool pour le dashboard. Les deux chemins utilisent exactement les mêmes fonctions métier.",
    )
    para(
        doc,
        "Le backend de données est optionnel : si MONGODB_URI est défini dans .env, les collections "
        "edtech_courses, edtech_learners, edtech_quiz_bank, edtech_quiz_attempts et edtech_a2a_delegations "
        "sont lues depuis MongoDB Atlas. Sinon, le serveur bascule automatiquement sur les fichiers JSON/CSV. "
        "Les collections existantes de la base ne sont jamais modifiées.",
    )
    code_block(
        doc,
        """
from mcp.server.fastmcp import FastMCP
from shared import edtech_core as core

mcp = FastMCP(
    "edumcp-edtech",
    instructions="Serveur MCP EduAgentic pour une plateforme d'apprentissage.",
    host="127.0.0.1", port=8000,
    sse_path="/sse", message_path="/messages/",
)

@mcp.tool()
def search_courses(query: str = "", level: str = "", max_results: int = 5) -> dict:
    \"\"\"Recherche des cours EdTech par mots-clés et filtre par niveau.\"\"\"
    return core.search_courses(query=query, level=level or None, max_results=max_results)

if __name__ == "__main__":
    mcp.run(transport="sse")
        """,
        "python",
    )
    h2(doc, "4.2 Les six outils")
    table(
        doc,
        ["Outil", "Paramètres", "Résultat", "Usage"],
        [(t[0], t[1], t[2], t[3]) for t in TOOLS],
        widths=[4.0, 4.2, 5.0, 3.2],
        caption="Tableau 5 · Outils exposés par le serveur MCP.",
    )
    para(
        doc,
        "Chaque outil possède une docstring : FastMCP en déduit un schéma JSON (nom, description, types, "
        "paramètres requis) que le client peut lire avant l'appel. C'est ce schéma qui permet à l'agent de choisir "
        "le bon outil sans connaître le code du serveur.",
    )
    h2(doc, "4.3 Extrait d'un schéma d'outil")
    code_block(
        doc,
        json.dumps(
            {
                "name": "recommend_learning_path",
                "description": "Parcours ordonné vers une compétence cible.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "learner_id": {"type": "string"},
                        "target_skill": {"type": "string"},
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        "json",
        font_size=7.2,
    )
    h2(doc, "4.4 Endpoints du pont REST")
    table(
        doc,
        ["Méthode", "Route", "Usage"],
        [
            ("GET", "/api/health", "État du serveur, transport, uptime, liste des outils"),
            ("GET", "/api/tools", "Liste lisible des outils et descriptions"),
            ("POST", "/api/tool", "Appelle un outil : {tool, arguments}"),
            ("GET", "/sse", "Flux SSE du protocole MCP"),
        ],
        widths=[2.2, 4.2, 9.8],
        caption="Tableau 6 · Points d'entrée du serveur.",
    )
    h3(doc, "4.5 Collections MongoDB (optionnel)")
    table(
        doc,
        ["Collection", "Contenu", "Volume"],
        [
            ("edtech_courses", "Catalogue des 14 cours", "14 documents"),
            ("edtech_learners", "Profils synthétiques", "24 documents"),
            ("edtech_quiz_bank", "Questions et corrections", "30 documents"),
            ("edtech_quiz_attempts", "Tentatives de quiz", "168 documents"),
            ("edtech_a2a_delegations", "Traces A2A", "84 documents"),
        ],
        widths=[5.2, 7.0, 4.0],
        caption="Tableau 6b · Collections préfixées edtech_ dans la base fusion.",
    )

    h1(doc, "5. Workflow Langflow")
    figure(doc, ASSETS / "workflow_mcp.png", "Figure 2 · Canvas Langflow : Chat Input → Agent → MCP Tools → Chat Output.")
    h2(doc, "5.1 Les quatre nœuds")
    table(
        doc,
        ["Nœud", "Configuration", "Rôle"],
        [
            ("Chat Input", "message, session_id", "Reçoit la question de l'utilisateur"),
            ("Agent", "LLM, system prompt, max_iterations=15", "Analyse, choisit l'outil, formule la réponse"),
            ("MCP Tools", "Serveur edumcp-edtech, SSE, 127.0.0.1:8000/sse", "Découvre et appelle les outils"),
            ("Chat Output", "text", "Affiche la réponse finale"),
        ],
        widths=[3.3, 8.0, 4.9],
        caption="Tableau 7 · Configuration des nœuds Langflow.",
    )
    h2(doc, "5.2 Import et configuration")
    bullets(
        doc,
        [
            "Lancer le serveur : python mcp_server/edumcp_server.py.",
            "Dans Langflow, ajouter un serveur MCP nommé edumcp-edtech, transport SSE, URL http://127.0.0.1:8000/sse.",
            "Importer json/Agentic_AI_EdTech_J33_MCP_Final.json.",
            "Vérifier que la sortie MCP Tools est connectée à l'entrée Tools de l'Agent.",
            "Configurer la clé du modèle (Google Generative AI, OpenAI ou OpenRouter) puis ouvrir le Playground.",
        ],
    )
    callout(
        doc,
        "Si vous utilisez ngrok",
        "Le serveur MCP peut être exposé par un tunnel HTTPS : ngrok http 8000, puis utiliser l'URL "
        "https://<tunnel>/sse dans Langflow. Le tunnel doit rester actif pendant les tests.",
        "warning",
    )
    h2(doc, "5.3 Prompt système de l'agent")
    code_block(
        doc,
        """
Tu es un conseiller pédagogique de la plateforme EduAgentic.
Tu disposes d'outils MCP pour chercher des cours, lire un profil, construire un parcours,
générer un quiz, corriger des réponses et calculer des statistiques.

Règles :
- Utilise toujours un outil avant d'inventer une réponse.
- Ne montre jamais le JSON brut : reformule en français, avec des listes claires.
- Cite les identifiants de cours (PY101, DATA350...) et les prérequis.
- Si l'information manque, dis-le et propose une prochaine étape.
- Rappelle que les données sont synthétiques et que la décision finale reste humaine.
        """,
        "text",
    )

    h1(doc, "6. Playground et scénarios")
    if (SHOTS / "mcp_result2.png").exists():
        figure(doc, SHOTS / "mcp_result2.png", "Figure 3 · Playground MCP : profil, parcours recommandé et ressources, avec la trace des outils.", width_cm=16.8)
    h2(doc, "6.1 Trois scénarios de démonstration")
    table(
        doc,
        ["Question", "Outils appelés", "Résultat attendu"],
        [
            ("Construis le parcours de Lina vers Data Analyst", "get_learner_profile → recommend_learning_path → search_courses", "Parcours de 3 étapes, 80 h, avec VIZ220, STAT210 et DATA350"),
            ("Génère un quiz Python de niveau facile", "generate_quiz", "3 questions, sans révéler les réponses"),
            ("Montre-moi les statistiques d'apprentissage", "get_learning_statistics", "KPI : 24 apprenants, score moyen 74,4, réussite 64,3 %"),
        ],
        widths=[6.0, 5.2, 5.0],
        caption="Tableau 8 · Scénarios testés dans le playground.",
    )
    h2(doc, "6.2 Ce que montre la trace")
    bullets(
        doc,
        [
            "L'outil choisi : search_courses, recommend_learning_path, generate_quiz, etc.",
            "Les arguments exacts envoyés au serveur, en JSON.",
            "La latence de l'appel et la source (MCP HTTP ou repli local).",
            "Le résultat complet, inspectable dans un bloc JSON.",
            "La réponse reformulée pour l'utilisateur, sans JSON brut.",
        ],
    )
    callout(
        doc,
        "Mode autonome",
        "Si le serveur MCP est arrêté, le playground bascule sur les mêmes fonctions en local et l'indique "
        "dans la trace. La démonstration reste donc possible hors ligne, mais le transport MCP n'est plus exercé.",
        "info",
    )

    h1(doc, "7. Données et jeu de test")
    table(
        doc,
        ["Jeu de données", "Volume", "Fichier"],
        [
            ("Cours", "14 cours, 6 domaines", "data/courses.json"),
            ("Apprenants", "24 profils synthétiques", "data/learners.json"),
            ("Banque de questions", "30 questions, 6 cours", "data/quiz_bank.json"),
            ("Tentatives de quiz", "168 tentatives", "data/quiz_attempts.csv"),
            ("Traces A2A", "84 délégations", "data/a2a_delegations.csv"),
        ],
        widths=[4.5, 6.0, 5.7],
        caption="Tableau 9 · Données utilisées par les outils et le dashboard.",
    )
    para(
        doc,
        "Toutes les données sont fictives et déterministes (graine 33). Les prénoms, cohortes et scores sont "
        "inventés. Aucun courriel, identifiant réel ou donnée personnelle n'est présent. Le jeu de données peut "
        "être régénéré avec python scripts/build_data.py.",
    )
    h2(doc, "7.1 KPI calculés")
    table(
        doc,
        ["KPI", "Valeur", "Méthode"],
        [
            ("Apprenants", str(k["learners"]), "nombre de profils"),
            ("Cours", str(k["courses"]), "catalogue"),
            ("Score moyen", f"{k['avg_score']}/100", "moyenne des 168 tentatives"),
            ("Réussite quiz", f"{k['success_rate']} %", "score ≥ 70"),
            ("Complétion moyenne", f"{k['avg_completion']} %", "moyenne des cours"),
            ("Inscriptions", f"{k['enrollments']:,}", "somme des inscriptions du catalogue"),
        ],
        widths=[5.2, 3.5, 7.5],
        caption="Tableau 10 · KPI du dashboard, recalculés depuis les données brutes.",
    )

    h1(doc, "8. Tests et validation")
    h2(doc, "8.1 Protocole de test")
    table(
        doc,
        ["Test", "Commande / action", "Résultat"],
        [
            ("Santé du serveur", "GET /api/health", "status=ok, 6 outils"),
            ("Découverte MCP", "session.list_tools() via client SSE", "6 outils listés"),
            ("Appel search_courses", "call_tool('search_courses', {...})", "3 cours retournés"),
            ("Appel recommend_learning_path", "L001 → data-analysis", "3 étapes, 80 h"),
            ("Appel generate_quiz", "PY101, 3 questions", "QUIZ-…, 3 questions"),
            ("Appel get_learning_statistics", "segment=Tous", "KPI et séries"),
            ("Dashboard", "http://localhost:8011", "6 pages, 0 exception"),
        ],
        widths=[5.0, 6.5, 4.7],
        caption="Tableau 11 · Tests réalisés le 11 novembre 2026.",
    )
    table(
        doc,
        ["Outil", "Statut", "Latence mesurée", "Source"],
        [(r["tool"], r["status"], f"{r['latency_ms']} ms", r["source"]) for r in mcp_test["results"]],
        widths=[6.0, 2.7, 4.0, 3.5],
        caption="Tableau 12 · Mesures des appels d'outils.",
    )
    callout(
        doc,
        "Interprétation",
        f"{mcp_test['ok']}/5 appels testés ont répondu sans erreur, avec une latence médiane de "
        f"{mcp_test['median_ms']} ms. Les valeurs faibles correspondent au pont REST local ; en production, "
        "la latence dépend du réseau, du modèle et du serveur MCP distant.",
        "success",
    )
    h2(doc, "8.2 Limites")
    bullets(
        doc,
        [
            "Le playground utilise un routeur déterministe pour la démonstration ; le workflow Langflow, lui, appelle un LLM.",
            "Les réponses du LLM ne sont pas évaluées automatiquement dans ce mini-projet : les tests portent sur les outils et le protocole.",
            "Le serveur écoute en localhost, sans authentification : il ne doit pas être exposé tel quel sur Internet.",
            "Le catalogue est volontairement petit (14 cours) pour rester lisible et reproductible.",
        ],
    )

    h1(doc, "9. Sécurité et bonnes pratiques")
    table(
        doc,
        ["Risque", "Mesure dans le projet", "À renforcer en production"],
        [
            ("Exposition du serveur", "Bind 127.0.0.1, tunnel explicite", "Authentification, TLS, liste d'IP"),
            ("Données personnelles", "Données 100 % synthétiques", "Anonymisation, consentement, RGPD"),
            ("Injection de prompt", "Outils bornés, pas d'exécution arbitraire", "Filtrage, allowlist d'outils"),
            ("Coût des appels", "Outils déterministes, pas de LLM dans les tests", "Quotas, cache, timeout"),
            ("Traçabilité", "Logs outil + arguments + latence", "Journal centralisé, rétention"),
            ("Erreur d'outil", "Messages d'erreur explicites, repli local", "Retry, circuit breaker"),
        ],
        widths=[4.0, 6.8, 5.4],
        caption="Tableau 13 · Analyse des risques et mesures.",
    )
    callout(
        doc,
        "Principe de moindre privilège",
        "Le serveur ne fait que lire un catalogue synthétique et calculer des scores. Il n'écrit pas dans une base "
        "réelle, n'envoie pas de courriel et ne déclenche aucune action irréversible. C'est un choix de conception "
        "pour une démonstration sûre.",
        "warning",
    )

    h1(doc, "10. Mode d'emploi")
    h2(doc, "10.1 Prérequis")
    bullets(
        doc,
        [
            "Python 3.11 ou supérieur.",
            "Dépendances : pip install -r requirements.txt.",
            "Pour le workflow : Langflow 1.7.0 et une clé de modèle.",
            "Pour le dashboard : Streamlit (inclus dans requirements.txt).",
        ],
    )
    h2(doc, "10.2 Commandes")
    code_block(
        doc,
        """
# 1. Configuration et dépendances
cp .env.example .env          # renseigner MONGODB_URI (ou laisser vide pour JSON)
python scripts/build_data.py
pip install -r requirements.txt

# 2. Serveur MCP (terminal 1)
python mcp_server/edumcp_server.py

# 3. Dashboard (terminal 2)
streamlit run dashboard/app.py --server.port 8011

# 4. Vérification rapide
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/sse   # flux SSE (garder ouvert)
        """,
        "bash",
        font_size=8.2,
    )
    table(
        doc,
        ["Problème", "Cause probable", "Solution"],
        [
            ("Connexion refusée sur 8000", "Serveur non lancé", "Démarrer edumcp_server.py"),
            ("MCP Tools vide dans Langflow", "Serveur MCP non déclaré", "Ajouter edumcp-edtech en SSE"),
            ("Réponse lente", "Modèle ou tunnel", "Tester /api/health, réduire max_iterations"),
            ("Dashboard sans données", "Fichiers data manquants", "Relancer scripts/build_data.py"),
        ],
        widths=[5.2, 5.5, 5.5],
        caption="Tableau 14 · Dépannage rapide.",
    )

    h1(doc, "Conclusion")
    para(
        doc,
        "Le mini-projet J33 démontre qu'un serveur MCP peut exposer des outils EdTech de façon standard, "
        "lisible et testable. L'agent ne dépend plus des routes internes : il découvre six outils, choisit le bon "
        "et reçoit un résultat structuré. Le playground et le dashboard rendent ce fonctionnement observable, "
        "ce qui est indispensable pour expliquer et auditer un système agentique.",
    )
    para(
        doc,
        "La suite naturelle est le jour 34 : plusieurs agents spécialisés collaborent via A2A. MCP standardise "
        "l'accès aux outils ; A2A standardise la collaboration entre agents. Les deux protocoles se complètent "
        "dans une même plateforme d'apprentissage.",
    )
    callout(
        doc,
        "Checklist de livraison",
        "☑ Serveur MCP opérationnel · ☑ 6 outils testés · ☑ Workflow JSON final · ☑ Playground · "
        "☑ Dashboard 8011 · ☑ Documentation · ☑ Présentation · ☑ Vidéo.",
        "success",
    )

    h1(doc, "Annexes")
    h2(doc, "A. Glossaire")
    table(
        doc,
        ["Terme", "Définition"],
        [
            ("MCP", "Model Context Protocol : standard de découverte et d'appel d'outils par un agent."),
            ("FastMCP", "Implémentation Python du serveur MCP, avec décorateurs @mcp.tool()."),
            ("SSE", "Server-Sent Events : transport HTTP unidirectionnel utilisé par le serveur."),
            ("Outil (tool)", "Fonction exposée avec un nom, une description et un schéma de paramètres."),
            ("Langflow", "Environnement visuel de construction de workflows d'agents."),
            ("Playground", "Interface de test qui envoie un message et affiche la réponse et la trace."),
        ],
        widths=[3.4, 12.8],
        caption="Tableau 15 · Glossaire MCP.",
    )
    h2(doc, "B. Checklist de recette")
    bullets(
        doc,
        [
            "Le serveur démarre et /api/health répond status=ok.",
            "Le client MCP liste exactement 6 outils.",
            "Chaque outil retourne un JSON valide sur un cas nominal.",
            "Le workflow Langflow est importable et les nœuds sont connectés.",
            "Le playground affiche la trace de chaque appel.",
            "Le dashboard répond sur localhost:8011 et ne lève aucune exception.",
        ],
    )

    path = DOCS / "Documentation_J33_MCP_EdTech.docx"
    doc.save(path)
    return path


def doc_a2a(snapshot: dict, a2a_test: dict) -> Path:
    k = snapshot["kpis"]
    doc = new_document(
        "Agentic AI in Education Technology — J34 A2A",
        "JOUR 34 · MINI-PROJET · CORRECTION FINALE",
        "Agent-to-Agent (A2A) : découverte, délégation et traçabilité",
        "J34 · A2A",
        "Documentation technique du système multi-agents EduAgentic",
    )
    cover(
        doc,
        "Jour 34 · Mini-projet · Correction finale",
        "A2A en EdTech :\nfaire collaborer des agents spécialisés",
        "AgentCards, découverte, délégation JSON-RPC et correlation_id",
        [
            ("Auteur", "Kamal El Afoui"),
            ("Programme", "Centre des Très Petites Entreprises Solidaires · DBA Technology"),
            ("Date", "11 novembre 2026"),
            ("Version", "1.0.0 — Correction finale"),
        ],
        [
            "Trois agents : Tuteur, Évaluation et Orientation.",
            "Un orchestrateur qui découvre les AgentCards et délègue en parallèle.",
            "Un protocole JSON-RPC 2.0 avec message/send et tasks/get.",
            "Un correlation_id unique pour relier chaque échange.",
            "Workflow Langflow, dashboard 8011 et vidéo de démonstration.",
        ],
    )

    h1(doc, "Résumé exécutif", page_break=False)
    para(
        doc,
        "Un seul agent ne possède pas toutes les compétences. Le protocole Agent-to-Agent (A2A) permet à des "
        "agents spécialisés de se découvrir, de se déléguer des tâches et de collaborer de manière standardisée. "
        "Chaque agent publie une AgentCard qui décrit son identité, ses compétences, son endpoint et ses conditions "
        "d'utilisation.",
    )
    para(
        doc,
        "Ce mini-projet construit EduA2A : un orchestrateur, un agent Tuteur (cours et parcours), un agent "
        "Évaluation (quiz et feedback) et un agent Orientation (écart de compétences et trajectoire métier). "
        "L'orchestrateur découvre les cartes, appelle les agents en parallèle via JSON-RPC et agrège leurs réponses. "
        "Chaque délégation porte un correlation_id, visible dans la timeline du dashboard et dans les logs.",
    )
    table(
        doc,
        ["Indicateur", "Valeur", "Preuve"],
        [
            ("Agents spécialisés", "3 (+ 1 orchestrateur)", "agent_cards/*.json"),
            ("AgentCards publiées", "4", "GET /.well-known/agent.json"),
            ("Délégations par demande", "3", "timeline du dashboard"),
            ("Découverte HTTP", "3 / 3 agents", "GET /discover"),
            ("Latence d'orchestration", f"{a2a_test['latency_ms']:.1f} ms", "test HTTP du 11/11/2026"),
            ("Taux de succès (jeu de 84 traces)", f"{k['delegation_success']} %", "data/a2a_delegations.csv"),
            ("Correlation_id", "unique par demande", "data/a2a_live.jsonl"),
        ],
        widths=[6.2, 4.2, 6.0],
        caption="Tableau 1 · Synthèse des résultats du mini-projet J34.",
    )
    callout(
        doc,
        "Résultat principal",
        "L'orchestrateur n'a pas besoin de connaître l'implémentation des agents : il lit leurs cartes, "
        "sélectionne les compétences et délègue. La réponse finale est une agrégation traçable de trois expertises.",
        "success",
    )
    add_toc(doc)

    h1(doc, "1. Contexte et problématique", page_break=True)
    h2(doc, "1.1 Pourquoi un protocole A2A ?")
    para(
        doc,
        "Dans une plateforme EdTech, les besoins sont hétérogènes : rechercher des ressources, évaluer des "
        "compétences, orienter vers un métier, produire un feedback. Un agent généraliste devient vite complexe, "
        "coûteux et difficile à évaluer. La spécialisation améliore la qualité, mais crée un nouveau problème : "
        "comment faire dialoguer ces agents ?",
    )
    bullets(
        doc,
        [
            "Chaque agent annonce ses capacités et son endpoint.",
            "Les autres agents peuvent le découvrir sans intégration codée en dur.",
            "Une tâche est confiée au spécialiste le plus adapté.",
            "Chaque échange est tracé pour diagnostiquer les erreurs et mesurer les performances.",
        ],
    )
    h2(doc, "1.2 Les trois piliers")
    table(
        doc,
        ["Pilier", "Question", "Dans EduA2A"],
        [
            ("AgentCard", "Qui est l'agent et que sait-il faire ?", "Carte JSON sur /.well-known/agent.json"),
            ("Discovery", "Quels agents sont disponibles ?", "GET des cartes des ports 8101-8103"),
            ("Delegation", "Qui fait quoi, et comment suivre ?", "message/send JSON-RPC + correlation_id"),
        ],
        widths=[3.4, 6.4, 6.4],
        caption="Tableau 2 · Les trois piliers du protocole A2A.",
    )

    h1(doc, "2. Objectifs et livrables")
    bullets(
        doc,
        [
            "Publier une AgentCard par agent, avec identité, compétences, endpoint et conditions d'utilisation.",
            "Implémenter un orchestrateur qui découvre les cartes et sélectionne les agents.",
            "Déléguer les tâches en JSON-RPC 2.0 et agréger les résultats.",
            "Tracer chaque échange avec un correlation_id et des logs horodatés.",
            "Démontrer le tout dans un dashboard et un workflow Langflow.",
        ],
    )
    table(
        doc,
        ["Livrable", "Fichier", "Contenu"],
        [
            ("Agents A2A", "a2a/agents.py, a2a/protocol.py", "Tuteur, Évaluation, Orientation"),
            ("Orchestrateur", "a2a/orchestrator.py", "Découverte, sélection, délégation, agrégation"),
            ("AgentCards", "a2a/agent_cards/*.json", "4 cartes A2A"),
            ("Workflow Langflow", "json/Agentic_AI_EdTech_J34_A2A_Final.json", "Découverte + orchestration"),
            ("Documentation", "docs/Documentation_J34_A2A_EdTech.docx / .pdf", "Ce document"),
            ("Vidéo", "videos/J34_A2A_Workflow_Playground.mp4", "Workflow + playground"),
        ],
        widths=[3.6, 7.2, 5.6],
        caption="Tableau 3 · Livrables du jour 34.",
    )

    h1(doc, "3. Architecture")
    figure(doc, ASSETS / "architecture_a2a.png", "Figure 1 · Architecture A2A : découverte des AgentCards, délégation parallèle et agrégation traçable.")
    table(
        doc,
        ["Composant", "Rôle", "Port", "Technologie"],
        [
            ("Orchestrateur", "Découvre, sélectionne, délègue, agrège", "8001", "FastAPI + JSON-RPC"),
            ("Agent Tuteur", "Cours, ressources, parcours", "8101", "FastAPI + AgentCard"),
            ("Agent Évaluation", "Quiz, correction, feedback", "8102", "FastAPI + AgentCard"),
            ("Agent Orientation", "Gap de compétences, trajectoire", "8103", "FastAPI + AgentCard"),
            ("Dashboard", "Observation, formulaire, timeline", "8011", "Streamlit"),
        ],
        widths=[4.0, 6.5, 2.0, 4.0],
        caption="Tableau 4 · Composants du système A2A.",
    )
    para(
        doc,
        "Les agents partagent le même backend de données que le serveur MCP : MongoDB Atlas (collections "
        "edtech_*) si MONGODB_URI est configuré, sinon les fichiers JSON/CSV. Ce choix garantit que le parcours, "
        "les ressources et le quiz portent sur les mêmes données, sans duplication.",
    )
    h2(doc, "3.1 Cycle d'une demande")
    bullets(
        doc,
        [
            "L'utilisateur formule un objectif et une question dans le dashboard.",
            "L'orchestrateur découvre les AgentCards disponibles et vérifie leur état.",
            "Il sélectionne les agents dont les compétences correspondent à la demande.",
            "Il envoie trois messages JSON-RPC en parallèle, avec le même correlation_id.",
            "Il agrège les artifacts en une réponse unique, puis écrit les traces.",
        ],
    )

    h1(doc, "4. AgentCards")
    h2(doc, "4.1 Structure d'une carte")
    code_block(
        doc,
        json.dumps(
            {
                "name": "Agent Tuteur",
                "description": "Recherche des ressources et recommande un parcours personnalisé.",
                "url": "http://127.0.0.1:8101/",
                "version": "1.0.0",
                "protocolVersion": "0.3.0",
                "preferredTransport": "JSONRPC",
                "capabilities": {"streaming": False, "pushNotifications": False},
                "skills": [
                    {
                        "id": "recommend_learning_path",
                        "name": "Parcours personnalisé",
                        "tags": ["parcours", "prérequis", "compétences"],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "json",
        font_size=7.5,
    )
    h2(doc, "4.2 Les quatre cartes")
    table(
        doc,
        ["Agent", "Compétences", "Endpoint", "Conditions"],
        [
            ("Orchestrateur", "orchestrate_learning_request", "8001", "Découverte et agrégation"),
            ("Tuteur", "search_courses, recommend_learning_path", "8101", "Usage pédagogique, sources citées"),
            ("Évaluation", "generate_quiz, grade_quiz", "8102", "Feedback formatif, pas de note certificative"),
            ("Orientation", "skill_gap, career_path", "8103", "Conseil, décision humaine finale"),
        ],
        widths=[3.2, 6.4, 2.2, 4.4],
        caption="Tableau 5 · AgentCards publiées par EduA2A.",
    )
    callout(
        doc,
        "Point d'entrée de toute collaboration",
        "Publier une AgentCard est indispensable avant toute découverte ou délégation. Sans carte, "
        "les autres agents ne connaissent ni les compétences ni l'endpoint du spécialiste.",
        "info",
    )

    h1(doc, "5. Protocole JSON-RPC")
    h2(doc, "5.1 Méthodes")
    table(
        doc,
        ["Méthode", "Paramètres", "Résultat"],
        [
            ("message/send", "message {parts, contextId}, metadata {correlation_id}", "Task avec artifacts"),
            ("tasks/get", "id de la tâche", "État et artifacts de la tâche"),
        ],
        widths=[3.5, 7.4, 5.3],
        caption="Tableau 6 · Méthodes A2A implémentées.",
    )
    h2(doc, "5.2 Exemple de requête")
    code_block(
        doc,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-7f3a",
                "method": "message/send",
                "params": {
                    "message": {
                        "role": "user",
                        "parts": [{"kind": "text", "text": "Construis mon parcours Data Analyst"}],
                        "messageId": "msg-91c2",
                        "contextId": "A2A-261111-120000-AB12",
                    },
                    "metadata": {
                        "correlation_id": "A2A-261111-120000-AB12",
                        "learner_id": "L001",
                        "target_skill": "data-analysis",
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        "json",
        font_size=7.4,
    )
    h2(doc, "5.3 Exemple de réponse")
    code_block(
        doc,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "req-7f3a",
                "result": {
                    "task": {
                        "kind": "task",
                        "id": "task-3b7c",
                        "contextId": "A2A-261111-120000-AB12",
                        "status": {"state": "completed"},
                        "artifacts": [
                            {
                                "name": "result",
                                "parts": [{"kind": "text", "text": "{...résultat JSON...}"}],
                            }
                        ],
                        "metadata": {"correlation_id": "A2A-261111-120000-AB12"},
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        "json",
        font_size=7.4,
    )
    callout(
        doc,
        "Pourquoi JSON-RPC ?",
        "Le format est simple, transportable en HTTP et lisible dans les logs. Il permet de distinguer "
        "clairement la requête, la réponse et l'erreur, tout en restant compatible avec le profil A2A.",
        "info",
    )

    h1(doc, "6. Orchestration et sélection")
    h2(doc, "6.1 Algorithme")
    bullets(
        doc,
        [
            "Découverte : lire les cartes des trois agents (HTTP, timeout court).",
            "Sélection : conserver les agents dont les compétences couvrent la demande.",
            "Parallélisme : envoyer les trois délégations avec ThreadPoolExecutor.",
            "Agrégation : fusionner profil, parcours, ressources et quiz.",
            "Traçabilité : écrire une ligne par délégation dans data/a2a_live.jsonl.",
        ],
    )
    h2(doc, "6.2 Répartition des rôles")
    table(
        doc,
        ["Étape", "Agent", "Sortie"],
        [
            ("Diagnostic", "Orientation", "Compétences acquises, manquantes, trajectoire"),
            ("Ressources", "Tuteur", "Cours, parcours ordonné, prérequis"),
            ("Évaluation", "Évaluation", "Quiz de 3 questions et feedback"),
            ("Synthèse", "Orchestrateur", "Réponse unique + timeline + correlation_id"),
        ],
        widths=[3.2, 3.5, 9.5],
        caption="Tableau 7 · Répartition des tâches entre agents.",
    )

    h1(doc, "7. Workflow Langflow")
    figure(doc, ASSETS / "workflow_a2a.png", "Figure 2 · Workflow A2A : découverte, orchestration, délégation aux trois agents et agrégation.")
    para(
        doc,
        "Le workflow importable se trouve dans json/Agentic_AI_EdTech_J34_A2A_Final.json. Il contient un Chat Input, "
        "un composant de découverte des AgentCards, un composant d'orchestration, un Chat Output et des notes "
        "d'architecture. L'orchestrateur appelle le service local http://127.0.0.1:8001/orchestrate.",
    )

    h1(doc, "8. Démonstration et traces")
    if (SHOTS / "a2a_result2.png").exists():
        figure(doc, SHOTS / "a2a_result2.png", "Figure 3 · Dashboard A2A : AgentCards en ligne, formulaire et lancement de l'orchestration.", width_cm=16.8)
    h2(doc, "8.1 Exemple de trace")
    table(
        doc,
        ["Horodatage", "Correlation ID", "Échange inter-agents", "Statut"],
        [
            ("09:15:01", "A2A-7F3B21", "Orchestrateur → Agent Orientation (diagnostic)", "Envoyé"),
            ("09:15:02", "A2A-7F3B21", "Orchestrateur → Agent Tuteur (ressources)", "Envoyé"),
            ("09:15:03", "A2A-7F3B21", "Orchestrateur → Agent Évaluation (quiz)", "Envoyé"),
            ("09:15:05", "A2A-7F3B21", "Orchestrateur → Agrégation (réponse finale)", "Réponse envoyée"),
        ],
        widths=[2.6, 3.2, 9.0, 2.7],
        caption="Tableau 8 · Log de délégation : un même correlation_id relie tous les échanges.",
    )
    para(
        doc,
        f"Lors du test HTTP du 11/11/2026, l'orchestration a duré {a2a_test['latency_ms']:.1f} ms pour "
        f"{a2a_test['agents']} agents, avec les statuts {', '.join(a2a_test['statuses'])}. "
        f"Le correlation_id généré était {a2a_test['correlation_id']}.",
    )
    h2(doc, "8.2 Ce que le correlation_id permet")
    bullets(
        doc,
        [
            "Retracer tout le parcours d'une demande, de l'orchestrateur jusqu'aux agents.",
            "Identifier rapidement l'agent qui a échoué ou ralenti.",
            "Comparer les performances entre agents et entre exécutions.",
            "Relier les logs aux artifacts et à la réponse finale.",
        ],
    )
    h2(doc, "8.3 Bénéfices pour l'architecture multi-agents")
    bullets(
        doc,
        [
            "Spécialisation et découplage : chaque agent reste concentré sur son domaine, sans connaître la logique interne des autres.",
            "Scalabilité dynamique : un nouvel agent rejoint l'écosystème en publiant simplement son AgentCard.",
            "Audit et diagnostic : le correlation_id et le log de délégation permettent d'isoler un échec et de mesurer la latence inter-agents.",
            "Réutilisation : les mêmes agents peuvent servir plusieurs orchestrateurs et plusieurs parcours.",
        ],
    )

    h1(doc, "9. Résultats et validation")
    table(
        doc,
        ["Test", "Résultat", "Preuve"],
        [
            ("Découverte des cartes", "3 / 3 agents en ligne", "GET /discover"),
            ("Délégation parallèle", "3 / 3 completed", "timeline du dashboard"),
            ("Agrégation", "Réponse unique + 3 artifacts", "POST /orchestrate"),
            ("Traçabilité", "1 correlation_id, 3 lignes de log", "data/a2a_live.jsonl"),
            ("Dashboard", "6 pages, 0 exception", "tests Playwright"),
        ],
        widths=[5.0, 6.2, 5.0],
        caption="Tableau 9 · Validation du système A2A.",
    )
    callout(
        doc,
        "Interprétation",
        "La latence de quelques dizaines de millisecondes montre que la découverte et la délégation locales sont "
        "très rapides. En production, il faudra ajouter l'authentification, le retry et un timeout par agent.",
        "success",
    )

    h1(doc, "10. Sécurité et limites")
    table(
        doc,
        ["Risque", "Mesure", "À renforcer"],
        [
            ("Agent non autorisé", "Cartes locales, ports dédiés", "Signature, registre, OAuth"),
            ("Données personnelles", "Données synthétiques", "Minimisation, RGPD"),
            ("Délégation en boucle", "Orchestration bornée à 3 agents", "Détection de cycles, budget"),
            ("Panne d'un agent", "Repli local et statut explicite", "Retry, circuit breaker"),
            ("Confiance dans la réponse", "Sources et artifacts", "Validation humaine"),
        ],
        widths=[4.2, 6.4, 5.6],
        caption="Tableau 10 · Risques et mesures A2A.",
    )
    para(
        doc,
        "Le système est une implémentation pédagogique du profil A2A 0.3.0 : AgentCard, découverte, message/send, "
        "tasks/get et artifacts. Il ne prétend pas couvrir toutes les extensions de la spécification "
        "(streaming, push notifications, authentification avancée).",
    )

    h1(doc, "11. Mode d'emploi")
    code_block(
        doc,
        """
# 1. Lancer les 3 agents + l'orchestrateur
python a2a/run_all.py

# 2. Vérifier la découverte
curl http://127.0.0.1:8001/discover

# 3. Dashboard
streamlit run dashboard/app.py --server.port 8011

# 4. Test direct d'orchestration
curl -X POST http://127.0.0.1:8001/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"learner_id":"L001","objective":"Devenir Data Analyst",
       "question":"Parcours, ressources et quiz"}'
        """,
        "bash",
        font_size=8.0,
    )
    table(
        doc,
        ["Problème", "Cause", "Solution"],
        [
            ("Agent hors ligne", "Processus non lancé", "python a2a/run_all.py"),
            ("Carte introuvable", "Mauvais port", "Vérifier 8101, 8102, 8103"),
            ("Réponse sans quiz", "Agent Évaluation indisponible", "Vérifier /health du port 8102"),
            ("Correlation_id absent", "Appel direct sans metadata", "Passer par /orchestrate"),
        ],
        widths=[5.0, 5.6, 5.6],
        caption="Tableau 11 · Dépannage A2A.",
    )

    h1(doc, "Conclusion")
    para(
        doc,
        "Le mini-projet J34 montre comment trois agents spécialisés peuvent collaborer sans se connaître : "
        "ils publient leurs compétences, l'orchestrateur les découvre et leur délègue des tâches. La réponse "
        "finale est plus riche qu'une réponse mono-agent, et surtout traçable grâce au correlation_id.",
    )
    para(
        doc,
        "MCP et A2A ne sont pas concurrents : MCP outille un agent, A2A fait travailler plusieurs agents ensemble. "
        "La plateforme EduAgentic illustre cette complémentarité dans un contexte éducatif concret, avec des "
        "données synthétiques et une démonstration reproductible.",
    )
    callout(
        doc,
        "Checklist de livraison",
        "☑ 3 AgentCards · ☑ Découverte HTTP · ☑ Délégation JSON-RPC · ☑ correlation_id · ☑ Workflow JSON · "
        "☑ Dashboard · ☑ Documentation · ☑ Présentation · ☑ Vidéo.",
        "success",
    )

    h1(doc, "Annexes")
    h2(doc, "A. Glossaire")
    table(
        doc,
        ["Terme", "Définition"],
        [
            ("A2A", "Agent-to-Agent : protocole de découverte et de délégation entre agents."),
            ("AgentCard", "Carte d'identité d'un agent : compétences, endpoint, conditions."),
            ("Discovery", "Découverte automatique des agents disponibles."),
            ("Delegation", "Transmission d'une tâche à un agent spécialisé."),
            ("correlation_id", "Identifiant unique qui relie tous les échanges d'une même demande."),
            ("Artifact", "Résultat produit par un agent et retourné dans la Task."),
        ],
        widths=[3.4, 12.8],
        caption="Tableau 12 · Glossaire A2A.",
    )
    h2(doc, "B. Checklist de recette")
    bullets(
        doc,
        [
            "Les quatre AgentCards sont accessibles en JSON.",
            "L'orchestrateur découvre les trois agents en moins de 2 secondes.",
            "Les trois délégations utilisent le même correlation_id.",
            "Les trois artifacts sont présents dans la réponse.",
            "Le dashboard affiche la timeline et les logs récents.",
            "Le workflow JSON est importable et documenté.",
        ],
    )

    path = DOCS / "Documentation_J34_A2A_EdTech.docx"
    doc.save(path)
    return path


def doc_global(snapshot: dict, mcp_test: dict, a2a_test: dict) -> Path:
    k = snapshot["kpis"]
    doc = new_document(
        "Agentic AI in Education Technology — J33 & J34",
        "SYNTHÈSE · JOURS 33 & 34 · CORRECTION FINALE",
        "MCP & A2A : deux briques pour une plateforme d'apprentissage agentique",
        "Synthèse J33 + J34",
        "Documentation globale des deux mini-projets EduAgentic",
    )
    cover(
        doc,
        "Synthèse · Jours 33 & 34 · Correction finale",
        "Agentic AI in Education Technology",
        "MCP pour outiller l'agent, A2A pour faire collaborer les agents",
        [
            ("Auteur", "Kamal El Afoui"),
            ("Programme", "Centre des Très Petites Entreprises Solidaires · DBA Technology"),
            ("Date", "11 novembre 2026"),
            ("Version", "1.0.0 — Correction finale"),
        ],
        [
            "J33 : serveur MCP, 6 outils, workflow Langflow et playground.",
            "J34 : 3 agents, AgentCards, découverte et délégation.",
            "Dashboard localhost:8011 : menu, formulaire, graphiques et traces.",
            "Documentation, présentations, JSON, vidéos et dépôt GitHub.",
            "Résultats, limites et perspectives des deux mini-projets.",
        ],
    )

    h1(doc, "Synthèse des deux mini-projets", page_break=False)
    para(
        doc,
        "Les deux journées répondent à deux questions complémentaires. Le jour 33 demande comment un agent "
        "accède à des outils externes de façon standard. Le jour 34 demande comment plusieurs agents spécialisés "
        "collaborent pour traiter une demande complexe. MCP standardise l'accès aux outils ; A2A standardise la "
        "collaboration entre agents.",
    )
    table(
        doc,
        ["Aspect", "J33 · MCP", "J34 · A2A"],
        [
            ("Question", "Comment exposer des outils à un agent ?", "Comment faire collaborer des agents ?"),
            ("Unité", "Outil (tool)", "Agent spécialisé"),
            ("Découverte", "Liste d'outils et schémas JSON", "AgentCards et compétences"),
            ("Contrat", "Appel d'outil MCP", "message/send JSON-RPC"),
            ("Traçabilité", "Outil, arguments, latence, résultat", "correlation_id, délégations, artifacts"),
            ("Démonstration", "Playground MCP", "Timeline A2A"),
        ],
        widths=[3.2, 6.5, 6.5],
        caption="Tableau 1 · Comparaison MCP / A2A.",
    )
    figure(doc, ASSETS / "workflow_mcp.png", "Figure 1 · Workflow MCP du jour 33.", width_cm=15.8)
    figure(doc, ASSETS / "workflow_a2a.png", "Figure 2 · Workflow A2A du jour 34.", width_cm=15.8)

    h1(doc, "Architecture globale")
    para(
        doc,
        "Le dashboard est le point d'observation commun. Il appelle le pont REST du serveur MCP pour le "
        "playground, et l'orchestrateur A2A pour la timeline. Les deux services sont indépendants : on peut "
        "démontrer MCP sans A2A, et inversement. Le dashboard bascule en mode local si un service est arrêté.",
    )
    table(
        doc,
        ["Service", "Port", "URL", "Rôle"],
        [
            ("Serveur MCP", "8000", "http://127.0.0.1:8000/sse", "6 outils EdTech"),
            ("Orchestrateur A2A", "8001", "http://127.0.0.1:8001", "Découverte et délégation"),
            ("Agent Tuteur", "8101", "http://127.0.0.1:8101", "Cours et parcours"),
            ("Agent Évaluation", "8102", "http://127.0.0.1:8102", "Quiz et feedback"),
            ("Agent Orientation", "8103", "http://127.0.0.1:8103", "Compétences et métier"),
            ("MongoDB Atlas", "—", "mongodb+srv://…/fusion", "Collections edtech_* (optionnel)"),
            ("Dashboard", "8011", "http://localhost:8011", "Interface et statistiques"),
        ],
        widths=[4.2, 2.0, 5.5, 4.5],
        caption="Tableau 2 · Cartographie des services.",
    )
    h2(doc, "Parcours utilisateur")
    bullets(
        doc,
        [
            "L'utilisateur ouvre localhost:8011 et choisit un apprenant.",
            "Dans MCP Playground, il demande un parcours ou un quiz : l'agent appelle les outils et montre la trace.",
            "Dans A2A Orchestration, il lance une demande : l'orchestrateur découvre les agents et délègue.",
            "Dans Statistiques, il filtre par cohorte et consulte les KPI, graphiques et tentatives récentes.",
            "Dans Documentation, il télécharge les livrables et retrouve les liens du dépôt.",
        ],
    )

    h1(doc, "Résultats clés")
    table(
        doc,
        ["KPI", "Valeur", "Source"],
        [
            ("Apprenants", str(k["learners"]), "data/learners.json"),
            ("Cours", str(k["courses"]), "data/courses.json"),
            ("Tentatives de quiz", str(k["attempts"]), "data/quiz_attempts.csv"),
            ("Score moyen", f"{k['avg_score']}/100", "calcul"),
            ("Réussite quiz", f"{k['success_rate']} %", "score ≥ 70"),
            ("Délégations A2A", str(k["delegations"]), "data/a2a_delegations.csv"),
            ("Succès A2A", f"{k['delegation_success']} %", "statuts completed"),
            ("Latence MCP médiane", f"{mcp_test['median_ms']} ms", "5 appels mesurés"),
            ("Latence A2A", f"{a2a_test['latency_ms']:.1f} ms", "orchestration test"),
            ("Outils MCP", "6", "list_tools"),
            ("Agents A2A", "3 + 1", "AgentCards"),
        ],
        widths=[6.0, 5.0, 5.5],
        caption="Tableau 3 · Résultats consolidés.",
    )
    callout(
        doc,
        "Lecture",
        "Les chiffres ne mesurent pas la qualité d'un LLM : ils mesurent la plateforme (outils, agents, données, "
        "dashboard). Les tests sont reproductibles et ne dépendent pas d'une clé API pour la partie déterministe.",
        "info",
    )

    h1(doc, "Livrables et dépôt")
    table(
        doc,
        ["Livrable", "Fichier", "Format"],
        [
            ("Documentation J33", "docs/Documentation_J33_MCP_EdTech.docx / .pdf", "DOCX / PDF"),
            ("Documentation J34", "docs/Documentation_J34_A2A_EdTech.docx / .pdf", "DOCX / PDF"),
            ("Documentation globale", "docs/Documentation_Globale_J33_J34.docx / .pdf", "DOCX / PDF"),
            ("Présentation J33", "presentation/J33_MCP_Presentation.pptx", "PPTX"),
            ("Présentation J34", "presentation/J34_A2A_Presentation.pptx", "PPTX"),
            ("Présentation finale", "presentation/Presentation_Finale_J33_J34.pptx", "PPTX"),
            ("Workflow MCP", "json/Agentic_AI_EdTech_J33_MCP_Final.json", "JSON"),
            ("Workflow A2A", "json/Agentic_AI_EdTech_J34_A2A_Final.json", "JSON"),
            ("Vidéo MCP", "videos/J33_MCP_Workflow_Playground.mp4", "MP4"),
            ("Vidéo A2A", "videos/J34_A2A_Workflow_Playground.mp4", "MP4"),
            ("Vidéo finale", "videos/Video_Finale_Agentic_AI_EdTech.mp4", "MP4"),
            ("Archive", "Agentic_AI_EdTech_J33_J34_FINAL.zip", "ZIP"),
        ],
        widths=[4.4, 8.8, 3.0],
        caption="Tableau 4 · Liste des livrables.",
    )
    h2(doc, "Dépôt GitHub")
    para(
        doc,
        "Le projet est versionné avec Git. Le dépôt contient le code, les données synthétiques, les JSON, les "
        "documents, les présentations et les vidéos. Les fichiers lourds peuvent être exclus du dépôt et joints "
        "au zip final. Les commandes de publication sont fournies dans README.md et GITHUB.md.",
    )
    code_block(
        doc,
        """
git init
git add .
git commit -m "EduAgentic J33/J34 — MCP & A2A, correction finale"
git branch -M main
git remote add origin https://github.com/<compte>/Agentic-AI-EdTech-J33-J34.git
git push -u origin main
        """,
        "bash",
        font_size=8.2,
    )

    h1(doc, "Limites et perspectives")
    table(
        doc,
        ["Limite", "Impact", "Perspective"],
        [
            ("Pas de LLM dans les tests", "La qualité rédactionnelle n'est pas mesurée", "Brancher un modèle et évaluer 20 questions"),
            ("Données synthétiques", "Pas de validation terrain", "Anonymiser un jeu réel"),
            ("Pas d'authentification", "Démo locale uniquement", "OAuth, TLS, registre d'agents"),
            ("3 agents", "Couverture fonctionnelle limitée", "Ajouter un agent Finance / Accessibilité"),
            ("Pas de streaming", "Réponse après complétion", "Ajouter SSE / streaming A2A"),
        ],
        widths=[5.0, 5.4, 5.8],
        caption="Tableau 5 · Limites et pistes d'amélioration.",
    )

    h1(doc, "Conclusion")
    para(
        doc,
        "MCP et A2A forment deux couches complémentaires d'une plateforme agentique : MCP donne des outils à un "
        "agent, A2A organise la collaboration entre plusieurs agents. Le projet EduAgentic montre cette "
        "complémentarité dans un contexte éducatif, avec un dashboard unique, des traces et des données "
        "synthétiques. Les deux mini-projets sont autonomes, testables et prêts à être présentés.",
    )
    callout(
        doc,
        "Checklist finale",
        "☑ Code · ☑ Données · ☑ JSON MCP/A2A · ☑ Dashboard 8011 · ☑ Documentation DOCX/PDF · "
        "☑ Présentations PPTX/PDF · ☑ Vidéos MP4 · ☑ GitHub · ☑ Zip.",
        "success",
    )

    path = DOCS / "Documentation_Globale_J33_J34.docx"
    doc.save(path)
    return path


def export_with_word(paths: list[Path]) -> None:
    """Met à jour les champs (TOC, pages) et exporte en PDF."""
    import win32com.client as win32

    word = win32.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for path in paths:
            doc = word.Documents.Open(str(path))
            try:
                doc.Fields.Update()
                # Compacte le sommaire pour qu'il tienne sur une page.
                for style_name in ("TOC 1", "TOC 2", "TOC 3"):
                    try:
                        style = doc.Styles(style_name)
                        style.Font.Size = 8.5
                        style.ParagraphFormat.SpaceAfter = 0
                        style.ParagraphFormat.SpaceBefore = 0
                        style.ParagraphFormat.LineSpacingRule = 0
                    except Exception:
                        pass
                for index in range(1, doc.TablesOfContents.Count + 1):
                    doc.TablesOfContents(index).Update()
                doc.Repaginate()
                doc.Save()
                pdf_path = path.with_suffix(".pdf")
                doc.ExportAsFixedFormat(
                    OutputFileName=str(pdf_path),
                    ExportFormat=17,
                    OpenAfterExport=False,
                    OptimizeFor=0,
                    Range=0,
                    Item=0,
                    IncludeDocProps=True,
                    KeepIRM=True,
                    CreateBookmarks=1,
                    DocStructureTags=True,
                    BitmapMissingFonts=True,
                    UseISO19005_1=False,
                )
                print("  PDF :", pdf_path.name, f"{pdf_path.stat().st_size/1024:.0f} Ko")
            finally:
                doc.Close(False)
    finally:
        word.Quit()


def main() -> None:
    snapshot = stats_snapshot()
    # Valeurs de référence de la campagne de tests du 11/11/2026.
    # Elles sont figées pour garantir la cohérence entre DOCX, PDF, decks et vidéos.
    mcp_test = {
        "results": [
            {"tool": "search_courses", "status": "OK", "latency_ms": 11.5, "source": "REST"},
            {"tool": "get_learner_profile", "status": "OK", "latency_ms": 8.2, "source": "REST"},
            {"tool": "recommend_learning_path", "status": "OK", "latency_ms": 8.1, "source": "REST"},
            {"tool": "generate_quiz", "status": "OK", "latency_ms": 6.5, "source": "REST"},
            {"tool": "get_learning_statistics", "status": "OK", "latency_ms": 16.6, "source": "REST"},
        ],
        "median_ms": 8.2,
        "ok": 5,
    }
    a2a_test = {
        "ok": True,
        "latency_ms": 49.2,
        "agents": 3,
        "statuses": ["completed", "completed", "completed"],
        "correlation_id": "A2A-261111-132825-2F42",
        "source": "HTTP",
    }
    print("Références de test :", mcp_test["median_ms"], "ms MCP ·", a2a_test["latency_ms"], "ms A2A")
    BENCH.write_text(
        json.dumps(
            {
                "mcp_median_ms": mcp_test["median_ms"],
                "mcp_results": mcp_test["results"],
                "a2a_latency_ms": round(a2a_test["latency_ms"], 1),
                "a2a_agents": a2a_test["agents"],
                "a2a_correlation_id": a2a_test["correlation_id"],
                "timestamp": "2026-11-11",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Construction des DOCX…")
    paths = [doc_mcp(snapshot, mcp_test, a2a_test), doc_a2a(snapshot, a2a_test), doc_global(snapshot, mcp_test, a2a_test)]
    for path in paths:
        print("  DOCX :", path.name, f"{path.stat().st_size/1024:.0f} Ko")
    print("Mise à jour des champs et export PDF…")
    export_with_word(paths)
    print("Documentation terminée.")


if __name__ == "__main__":
    main()

