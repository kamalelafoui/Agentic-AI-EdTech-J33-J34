# -*- coding: utf-8 -*-
"""Schémas d'architecture et de workflow pour la documentation et les slides."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

NAVY = "#0B2340"
NAVY2 = "#14365C"
GOLD = "#F4B400"
TEAL = "#16A6A1"
BLUE = "#3B82C4"
LIGHT = "#F4F7FB"
BORDER = "#DCE7F2"
INK = "#12263F"
MUTED = "#6B7C93"
PURPLE = "#7A5AA6"
GREEN = "#2E8B72"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.facecolor": LIGHT,
        "figure.facecolor": LIGHT,
    }
)


def canvas(figsize=(16, 9)):
    fig, ax = plt.subplots(figsize=figsize, dpi=190)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor(LIGHT)
    return fig, ax


def rr(ax, x, y, w, h, fc="white", ec=BORDER, lw=1.4, radius=0.18, z=2, alpha=1.0):
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=z,
        alpha=alpha,
    )
    ax.add_patch(box)
    return box


def label(ax, x, y, text, size=11, color=INK, weight="normal", ha="left", va="center", z=5):
    ax.text(x, y, text, fontsize=size, color=color, weight=weight, ha=ha, va=va, zorder=z)


def arrow(ax, xy1, xy2, color=NAVY, lw=1.8, style="-|>", ls="-", rad=0.0, z=4):
    ax.add_patch(
        FancyArrowPatch(
            xy1,
            xy2,
            arrowstyle=style,
            mutation_scale=15,
            color=color,
            linewidth=lw,
            linestyle=ls,
            connectionstyle=f"arc3,rad={rad}",
            zorder=z,
        )
    )


def title(ax, kicker, main, sub=None):
    ax.add_patch(Rectangle((0, 8.55), 16, 0.45, facecolor=NAVY, edgecolor="none", zorder=1))
    label(ax, 0.45, 8.78, kicker.upper(), 9, GOLD, "bold")
    label(ax, 0.45, 8.08, main, 22, INK, "bold")
    if sub:
        label(ax, 0.45, 7.68, sub, 10.5, MUTED)


def footer(ax, text):
    ax.plot([0.45, 15.55], [0.38, 0.38], color=BORDER, lw=1)
    label(ax, 0.45, 0.2, text, 8.5, MUTED)
    label(ax, 15.55, 0.2, "EduAgentic · J33/J34", 8.5, MUTED, ha="right")


def node(ax, x, y, w, h, title_text, lines, color=NAVY, badge=None, fc="white"):
    rr(ax, x, y, w, h, fc=fc, ec=BORDER)
    ax.add_patch(
        FancyBboxPatch(
            (x, y + h - 0.44),
            w,
            0.44,
            boxstyle="round,pad=0.02,rounding_size=0.15",
            facecolor=color,
            edgecolor="none",
            zorder=3,
        )
    )
    label(ax, x + 0.18, y + h - 0.22, title_text, 10.5, "white", "bold")
    yy = y + h - 0.72
    for line in lines:
        label(ax, x + 0.18, yy, line, 8.8, MUTED)
        yy -= 0.27


def arch_mcp():
    fig, ax = canvas()
    title(
        ax,
        "Jour 33 · Model Context Protocol",
        "Architecture MCP — exposer les outils EdTech à un agent",
        "L'agent découvre les outils, choisit celui qui répond à la demande et reçoit un résultat structuré.",
    )
    node(ax, 0.45, 4.55, 2.35, 2.05, "1 · Utilisateur", ["Question en français", "Playground / Langflow", "Chat Input"], BLUE, "Client")
    node(ax, 3.35, 4.35, 3.0, 2.45, "2 · Agent Langflow", ["LLM + raisonnement", "MCP Tools connecté", "Choisit l'outil et les args"], PURPLE, "Agent")
    node(ax, 10.2, 4.55, 2.35, 2.05, "4 · Réponse", ["Réponse naturelle", "JSON brut masqué", "Chat Output"], GREEN, "Output")
    node(
        ax,
        6.95,
        3.35,
        2.85,
        3.75,
        "3 · Serveur MCP",
        [
            "FastMCP · SSE /sse",
            "127.0.0.1:8000",
            "6 outils exposés",
            "search_courses",
            "get_learner_profile",
            "recommend_learning_path",
            "generate_quiz · grade_quiz",
            "get_learning_statistics",
        ],
        GOLD,
        "MCP",
    )
    node(ax, 3.1, 0.85, 3.5, 1.65, "Données EdTech", ["14 cours · 24 apprenants", "168 tentatives · 84 traces", "MongoDB Atlas ou JSON", "100 % synthétique"], TEAL, "Data")
    node(ax, 7.25, 0.85, 3.2, 1.65, "Dashboard 8011", ["Pont REST : /api/tool", "KPI, graphiques, traces", "Mode repli local"], NAVY, "UI")
    node(ax, 11.2, 0.85, 3.2, 1.65, "Traçabilité", ["Outil + arguments", "Latence + résultat", "Logs JSON"], MUTED, "Audit")

    arrow(ax, (2.8, 5.55), (3.35, 5.55), NAVY, 2)
    arrow(ax, (6.35, 5.55), (6.95, 5.55), GOLD, 2)
    arrow(ax, (6.95, 4.95), (6.35, 4.95), TEAL, 1.8)
    arrow(ax, (9.8, 5.55), (10.2, 5.55), GREEN, 2)
    arrow(ax, (8.35, 3.35), (6.7, 2.5), TEAL, 1.5, ls="--")
    arrow(ax, (9.8, 1.65), (10.2, 4.55), MUTED, 1.3, ls=":")

    footer(ax, "MCP · transport SSE · découverte automatique des outils · Langflow 1.7 · FastMCP")
    fig.savefig(ASSETS / "architecture_mcp.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def arch_a2a():
    fig, ax = canvas()
    title(
        ax,
        "Jour 34 · Agent-to-Agent",
        "Architecture A2A — découvrir, déléguer, agréger",
        "Chaque agent publie une AgentCard. L'orchestrateur sélectionne les spécialistes et trace chaque échange.",
    )
    node(ax, 0.45, 4.2, 2.2, 2.0, "Utilisateur", ["Objectif d'apprentissage", "Question / tâche", "Chat Input"], BLUE, "Client")
    node(ax, 3.15, 3.6, 2.55, 3.1, "Orchestrateur", ["Découverte des cartes", "Sélection des agents", "Délégation parallèle", "Agrégation", "correlation_id"], NAVY, "A2A")
    nodes = [
        (6.65, 5.25, "Agent Tuteur", ["Cours & ressources", "Parcours, prérequis", "search_courses", "port 8101"], TEAL, "8101"),
        (6.65, 2.95, "Agent Évaluation", ["Quiz formatif", "Correction · feedback", "port 8102"], GOLD, "8102"),
        (6.65, 0.75, "Agent Orientation", ["Écart de compétences", "Trajectoire métier", "skill_gap · port 8103"], BLUE, "8103"),
    ]
    for x, y, name, lines, color, port in nodes:
        node(ax, x, y, 2.9, 1.95, name, lines, color, port)
    node(ax, 10.45, 3.55, 2.55, 2.4, "Agrégation", ["Réponse unique", "3 artifacts", "Timeline + logs"], GREEN, "Output")
    node(ax, 10.45, 0.75, 2.55, 1.75, "Dashboard 8011", ["AgentCards", "Timeline", "KPI A2A"], NAVY, "UI")
    node(ax, 13.4, 3.55, 2.15, 1.55, "Traçabilité", ["delegation.jsonl", "correlation_id", "latence"], MUTED, "Audit")
    arrow(ax, (2.65, 5.2), (3.15, 5.2), NAVY, 2)
    for x, y, name, lines, color, port in nodes:
        mid = y + 0.95
        arrow(ax, (5.7, 4.9), (6.65, mid), color, 1.4, ls="--", rad=0.05)
        arrow(ax, (5.7, 4.6), (6.65, mid), color, 2, rad=-0.05)
    arrow(ax, (9.55, 5.2), (10.45, 5.0), GREEN, 2)
    arrow(ax, (11.7, 3.55), (11.7, 2.5), NAVY, 1.6)
    arrow(ax, (10.45, 4.3), (13.4, 4.3), MUTED, 1.3, ls=":")
    label(ax, 5.15, 6.4, "discover (AgentCard)", 7.3, MUTED)
    label(ax, 5.15, 4.15, "message/send", 7.3, NAVY)
    label(ax, 11.9, 2.95, "résultat", 7.5, NAVY)
    footer(ax, "A2A 0.3 · JSON-RPC 2.0 · AgentCards /.well-known/agent.json · 3 agents + 1 orchestrateur")
    fig.savefig(ASSETS / "architecture_a2a.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def workflow_mcp():
    fig, ax = canvas((16, 8.6))
    ax.set_facecolor("#F7F9FC")
    # dotted canvas
    for x in range(0, 17, 1):
        ax.plot([x, x], [0, 9], color="#E8EEF6", lw=0.4, zorder=0)
    for y in range(0, 10, 1):
        ax.plot([0, 16], [y, y], color="#E8EEF6", lw=0.4, zorder=0)
    title(ax, "Workflow Langflow · J33", "MCP Tools : le canvas du mini-projet", "Chat Input → Agent → MCP Tools → Chat Output")
    node(ax, 0.55, 4.2, 2.55, 1.9, "Chat Input", ["message", "Playground", "session_id"], BLUE, "Input")
    node(ax, 4.0, 3.8, 3.5, 2.7, "Agent", ["LLM : gemini / gpt", "system prompt EdTech", "max_iterations = 15", "outils MCP attachés"], PURPLE, "Agent")
    node(ax, 8.35, 3.25, 3.75, 3.8, "MCP Tools", ["Serveur : edumcp-edtech", "Transport : SSE", "URL : 127.0.0.1:8000/sse", "", "6 outils découvrables", "JSON Schema auto"], GOLD, "MCP")
    node(ax, 12.95, 4.2, 2.45, 1.9, "Chat Output", ["text", "réponse naturelle", "sources / cours"], GREEN, "Output")
    # tool list panel
    rr(ax, 8.55, 0.65, 3.35, 2.0, fc="white", ec="#E5D59B")
    label(ax, 8.72, 2.42, "Outils exposés", 9.5, "#7A5B00", "bold")
    tools = ["search_courses", "get_learner_profile", "recommend_learning_path", "generate_quiz / grade_quiz", "get_learning_statistics"]
    for i, tool in enumerate(tools):
        label(ax, 8.75, 2.12 - i * 0.27, f"• {tool}", 7.4, MUTED)
    # note panel
    rr(ax, 0.55, 0.65, 7.35, 2.55, fc="#FFFDF5", ec="#F0E1B2")
    label(ax, 0.75, 2.95, "Note d'import", 10, "#7A5B00", "bold")
    notes = [
        "1. Démarrer le serveur : python mcp_server/edumcp_server.py",
        "2. Dans Langflow, ajouter un serveur MCP nommé edumcp-edtech (SSE).",
        "3. Connecter la sortie MCP Tools à l'entrée Tools de l'Agent.",
        "4. Configurer la clé du modèle, puis ouvrir le Playground.",
    ]
    for i, note in enumerate(notes):
        label(ax, 0.75, 2.6 - i * 0.34, note, 8.2, MUTED)
    arrow(ax, (3.1, 5.15), (4.0, 5.15), NAVY, 2.2)
    arrow(ax, (7.5, 5.15), (8.35, 5.15), GOLD, 2.2)
    arrow(ax, (12.1, 5.15), (12.95, 5.15), GREEN, 2.2)
    label(ax, 3.18, 5.45, "message", 7.8, BLUE)
    label(ax, 7.58, 5.45, "tools", 7.8, "#8A6100")
    label(ax, 12.18, 5.45, "response", 7.8, GREEN)
    footer(ax, "Workflow importable : json/Agentic_AI_EdTech_J33_MCP_Final.json · 4 noeuds + note")
    fig.savefig(ASSETS / "workflow_mcp.png", bbox_inches="tight", facecolor="#F7F9FC")
    plt.close(fig)


def workflow_a2a():
    fig, ax = canvas((16, 8.6))
    ax.set_facecolor("#F7F9FC")
    for x in range(0, 17, 1):
        ax.plot([x, x], [0, 9], color="#E8EEF6", lw=0.4, zorder=0)
    for y in range(0, 10, 1):
        ax.plot([0, 16], [y, y], color="#E8EEF6", lw=0.4, zorder=0)
    title(ax, "Workflow Langflow · J34", "Orchestration A2A : découvrir, déléguer, agréger", "Chat Input → Découverte → Orchestrateur → 3 agents → Chat Output")
    node(ax, 0.45, 4.55, 2.2, 1.8, "Chat Input", ["objectif", "learner_id", "question"], BLUE, "Input")
    node(ax, 3.0, 4.55, 2.55, 1.8, "Découverte", ["GET AgentCards", "3 agents en ligne", "skills + tags"], TEAL, "Cards")
    node(ax, 5.9, 3.65, 3.1, 3.0, "Orchestrateur", ["sélection des agents", "3 délégations parallèles", "agrégation", "correlation_id"], NAVY, "A2A")
    agent_data = [
        (9.55, 5.55, "Agent Tuteur", "cours · parcours", TEAL, "8101"),
        (9.55, 3.15, "Agent Évaluation", "quiz · feedback", GOLD, "8102"),
        (9.55, 0.75, "Agent Orientation", "gap · carrière", BLUE, "8103"),
    ]
    for x, y, name, sub, color, port in agent_data:
        node(ax, x, y, 2.55, 1.6, name, [sub, "AgentCard publiée", f"port {port}"], color, port)
    node(ax, 5.9, 0.75, 3.1, 1.55, "Chat Output", ["réponse consolidée", "timeline + artifacts", "correlation_id"], GREEN, "Output")
    rr(ax, 0.45, 0.55, 4.95, 2.95, fc="#FFFDF5", ec="#F0E1B2")
    label(ax, 0.65, 3.2, "Ce que montre le workflow", 9.5, "#7A5B00", "bold")
    notes = [
        "• Chaque agent est indépendant :",
        "  un port, une carte, un endpoint JSON-RPC.",
        "• L'orchestrateur délègue puis agrège.",
        "• Le correlation_id relie les 3 échanges.",
        "",
        "Sortie : parcours + ressources + quiz",
        "A2A-261111-120000-AB12",
    ]
    for i, note in enumerate(notes):
        label(ax, 0.65, 2.85 - i * 0.31, note, 7.9, MUTED)
    arrow(ax, (2.65, 5.45), (3.0, 5.45), NAVY, 2)
    arrow(ax, (5.55, 5.45), (5.9, 5.45), TEAL, 2)
    for x, y, name, sub, color, port in agent_data:
        arrow(ax, (9.0, 5.1), (9.55, y + 0.8), color, 1.8, rad=0.04)
    arrow(ax, (7.45, 3.65), (7.45, 2.3), GREEN, 2)
    label(ax, 7.58, 2.98, "agrégation", 7.5, GREEN)
    footer(ax, "Workflow importable : json/Agentic_AI_EdTech_J34_A2A_Final.json · découverte + orchestration")
    fig.savefig(ASSETS / "workflow_a2a.png", bbox_inches="tight", facecolor="#F7F9FC")
    plt.close(fig)


def main():
    arch_mcp()
    arch_a2a()
    workflow_mcp()
    workflow_a2a()
    print("Schémas générés dans", ASSETS)


if __name__ == "__main__":
    main()
