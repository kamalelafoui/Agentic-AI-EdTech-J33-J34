# -*- coding: utf-8 -*-
"""Dashboard EduAgentic — MCP & A2A pour l'éducation.

Lancement :
    streamlit run dashboard/app.py --server.port 8011

Le dashboard fonctionne en mode connecté (serveurs MCP/A2A lancés) ou en mode
autonome : les mêmes fonctions métier sont alors appelées en local.
"""
from __future__ import annotations

import html
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import mistune
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import a2a_core  # noqa: E402
from shared import edtech_core as core  # noqa: E402

ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
PRESENTATION = ROOT / "presentation"
VIDEOS = ROOT / "videos"
JSON_DIR = ROOT / "json"

MCP_HEALTH = "http://127.0.0.1:8000/api/health"
MCP_TOOL = "http://127.0.0.1:8000/api/tool"
A2A_HEALTH = "http://127.0.0.1:8001/health"
A2A_ORCHESTRATE = "http://127.0.0.1:8001/orchestrate"
A2A_DISCOVER = "http://127.0.0.1:8001/discover"

NAVY = "#0B2340"
GOLD = "#F4B400"
TEAL = "#16A6A1"
BLUE = "#3B82C4"
RED = "#E4572E"
MUTED = "#6B7C93"
PALETTE = [NAVY, GOLD, TEAL, BLUE, "#8E6BBF", "#7A8CA6"]

MENU = [
    "🏠 Vue d'ensemble",
    "🧩 MCP Playground",
    "🤝 A2A Orchestration",
    "📊 Statistiques",
    "📚 Documentation",
    "⚙️ Architecture",
]

st.set_page_config(
    page_title="EduAgentic · Dashboard",
    page_icon=str(ASSETS / "logo_mark.png") if (ASSETS / "logo_mark.png").exists() else "🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Style
# --------------------------------------------------------------------------- #
def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root {
            --navy:#0B2340; --navy-2:#14365C; --gold:#F4B400; --teal:#16A6A1;
            --blue:#3B82C4; --bg:#F4F7FB; --ink:#12263F; --muted:#6B7C93;
        }
        html, body, [class*="css"] { font-family:'Inter','Segoe UI',sans-serif; }
        .stApp { background:radial-gradient(1200px 600px at 85% -10%, #E9F3FF 0%, var(--bg) 45%, #F8FAFD 100%); }
        [data-testid="stHeader"] { background:transparent; }
        #MainMenu {visibility:hidden;} footer {visibility:hidden;}
        .block-container { padding-top:1.3rem; padding-bottom:3rem; max-width:1450px; }

        [data-testid="stSidebar"] {
            background:linear-gradient(180deg,#071A30 0%,#0B2340 55%,#0E2B4D 100%);
            border-right:1px solid rgba(255,255,255,.06);
        }
        [data-testid="stSidebar"] * { color:#E9F1FA !important; }
        [data-testid="stSidebar"] .stRadio > div { gap:.28rem; }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius:10px; padding:8px 10px; margin:2px 0; transition:.15s; cursor:pointer;
            border-left:3px solid transparent;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:rgba(255,255,255,.07); }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background:linear-gradient(90deg,rgba(244,180,0,.22),rgba(244,180,0,.04));
            border-left:3px solid var(--gold);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label > div > div:first-child { display:none; }
        [data-testid="stSidebar"] [role="radiogroup"] p { margin:0; font-size:.84rem; font-weight:600; }
        [data-testid="stAppDeployButton"], [data-testid="stToolbar"] { display:none !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] img { border-radius:14px; }

        .hero {
            position:relative; overflow:hidden; border-radius:22px; padding:30px 34px;
            background:linear-gradient(115deg,#071A30 0%,#0B2340 52%,#17446F 100%);
            color:#fff; box-shadow:0 18px 40px rgba(11,35,64,.18); margin-bottom:20px;
            border:1px solid rgba(255,255,255,.08);
        }
        .hero:after {
            content:""; position:absolute; right:-90px; top:-110px; width:330px; height:330px;
            border-radius:50%; background:radial-gradient(circle,rgba(244,180,0,.32),rgba(244,180,0,0) 64%);
        }
        .hero:before {
            content:""; position:absolute; right:120px; bottom:-130px; width:260px; height:260px;
            border-radius:50%; border:42px solid rgba(22,166,161,.18);
        }
        .hero-kicker { font-size:.76rem; letter-spacing:.18em; font-weight:800; color:var(--gold); text-transform:uppercase; }
        .hero h1 { font-size:2.15rem; line-height:1.12; margin:.45rem 0 .55rem; font-weight:800; letter-spacing:-.02em; }
        .hero p { color:#C9D8E8; font-size:1.02rem; max-width:850px; margin:0; line-height:1.55; }
        .hero .chips { display:flex; gap:9px; flex-wrap:wrap; margin-top:18px; position:relative; z-index:2; }
        .chip { font-size:.76rem; font-weight:700; padding:6px 11px; border-radius:999px;
                background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.14); color:#EAF2FB; }
        .chip.gold { background:rgba(244,180,0,.16); border-color:rgba(244,180,0,.35); color:#FFD666; }
        .chip.teal { background:rgba(22,166,161,.15); border-color:rgba(22,166,161,.35); color:#8FE3DF; }

        .grid { display:grid; gap:14px; }
        .metrics { grid-template-columns:repeat(5,minmax(0,1fr)); }
        @media(max-width:1150px){ .metrics{grid-template-columns:repeat(2,minmax(0,1fr));} }
        .metric {
            background:#fff; border:1px solid #E4ECF5; border-radius:16px; padding:16px 16px 14px;
            box-shadow:0 6px 18px rgba(18,38,63,.05); display:flex; gap:12px; align-items:flex-start;
        }
        .metric .ico { width:38px; height:38px; border-radius:11px; display:flex; align-items:center;
            justify-content:center; font-size:1.05rem; background:#EEF5FC; flex:none; }
        .metric .val { font-size:1.55rem; font-weight:800; color:var(--ink); line-height:1.05; letter-spacing:-.02em; }
        .metric .lab { font-size:.78rem; color:var(--muted); font-weight:600; margin-top:4px; }
        .metric .delta { font-size:.72rem; font-weight:700; color:var(--teal); margin-top:5px; }

        .card { background:#fff; border:1px solid #E4ECF5; border-radius:18px; padding:20px 22px;
                box-shadow:0 8px 22px rgba(18,38,63,.05); height:100%; }
        .card h3 { margin:0 0 .4rem; font-size:1.05rem; color:var(--ink); font-weight:800; }
        .card p { color:var(--muted); font-size:.9rem; line-height:1.55; margin:.2rem 0; }
        .card .tag { display:inline-block; margin-top:12px; font-size:.72rem; font-weight:800;
            color:var(--navy); background:#EEF5FC; border-radius:999px; padding:5px 10px; }
        .section-title { font-size:1.12rem; font-weight:800; color:var(--ink); margin:8px 0 10px; letter-spacing:-.01em; }
        .section-sub { color:var(--muted); font-size:.86rem; margin-top:-6px; margin-bottom:12px; }

        .status { display:inline-flex; align-items:center; gap:7px; font-size:.75rem; font-weight:700;
            padding:6px 10px; border-radius:999px; background:#EAF8F4; color:#0C7B67; }
        .status.off { background:#FDECEA; color:#B23B2E; }
        .dot { width:7px; height:7px; border-radius:50%; background:currentColor; box-shadow:0 0 0 3px rgba(0,0,0,.05); }

        .agent-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
        @media(max-width:1200px){ .agent-grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
        .agent { background:#fff; border:1px solid #E4ECF5; border-radius:16px; padding:15px 16px;
                 box-shadow:0 6px 18px rgba(18,38,63,.05); position:relative; overflow:hidden; }
        .agent .top { display:flex; align-items:center; gap:9px; }
        .agent .avatar { width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
                         font-size:1rem; background:#EEF5FC; }
        .agent .name { font-weight:800; font-size:.86rem; color:var(--ink); }
        .agent .port { font-size:.68rem; color:var(--muted); font-weight:600; }
        .agent .desc { font-size:.75rem; color:var(--muted); line-height:1.45; margin:9px 0; min-height:34px; }
        .agent .skill { display:inline-block; font-size:.64rem; font-weight:700; padding:3px 7px; border-radius:6px;
                        background:#F1F5FA; color:#47607B; margin:2px 2px 0 0; }

        .trace { border-left:3px solid #DCE8F4; margin-left:9px; padding-left:18px; }
        .trace-item { position:relative; padding:10px 0 10px 2px; }
        .trace-item:before { content:""; position:absolute; left:-25px; top:15px; width:11px; height:11px; border-radius:50%;
                             background:var(--teal); border:2px solid #fff; box-shadow:0 0 0 2px #DCE8F4; }
        .trace-item.failed:before { background:var(--red); }
        .trace-head { display:flex; gap:8px; align-items:center; flex-wrap:wrap; font-size:.8rem; }
        .trace-head b { color:var(--ink); }
        .trace-meta { font-size:.7rem; color:var(--muted); margin-top:4px; }
        .badge { font-size:.66rem; font-weight:800; padding:3px 7px; border-radius:6px; background:#EAF8F4; color:#0C7B67; }
        .badge.local { background:#FFF7E0; color:#8A6100; }
        .badge.failed { background:#FDECEA; color:#B23B2E; }

        .answer { background:linear-gradient(180deg,#FFFFFF,#F7FAFE); border:1px solid #DCE8F4; border-radius:16px;
                  padding:18px 20px; line-height:1.6; }
        .answer h3 { color:var(--navy); margin:0 0 8px; font-size:1.05rem; }
        .answer p { margin:.35rem 0; color:#33475F; font-size:.88rem; }
        .answer ul, .answer ol { margin:6px 0 10px 18px; padding:0; }
        .answer li { margin:3px 0; color:#33475F; font-size:.86rem; line-height:1.55; }
        .answer strong { color:var(--navy); }
        .answer code { background:#EEF5FC; color:#0B4A78; padding:1px 4px; border-radius:4px; font-size:.8rem; }
        .answer blockquote { border-left:4px solid var(--gold); background:#FFF9E8; margin:12px 0 0; padding:8px 12px;
                             color:#5F4B00; font-size:.83rem; border-radius:0 8px 8px 0; }
        .answer blockquote p { color:#5F4B00; font-size:.83rem; }

        .doc-row { display:flex; align-items:center; justify-content:space-between; gap:12px;
                   border-bottom:1px solid #EDF2F8; padding:11px 2px; }
        .doc-row:last-child { border-bottom:none; }
        .doc-name { font-size:.86rem; font-weight:700; color:var(--ink); }
        .doc-meta { font-size:.72rem; color:var(--muted); }
        .pill { font-size:.68rem; font-weight:800; padding:4px 8px; border-radius:7px; background:#EEF5FC; color:#2D5A88; }

        .footer { margin-top:26px; padding-top:14px; border-top:1px solid #DDE7F1; color:#8193A8;
                  font-size:.74rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }

        .stButton > button, .stFormSubmitButton > button {
            border-radius:10px; border:1px solid #D8E4F0; font-weight:700; font-size:.86rem;
            transition:.18s; background:#fff; color:var(--navy);
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover { border-color:var(--gold); color:var(--navy); }
        .stFormSubmitButton > button {
            background:linear-gradient(135deg,#F4B400,#FFD45C); border:none; color:#17263A;
            box-shadow:0 6px 16px rgba(244,180,0,.3);
        }
        [data-testid="stForm"] { background:#fff; border:1px solid #E4ECF5; border-radius:16px; padding:16px 18px;
                                 box-shadow:0 6px 18px rgba(18,38,63,.04); }
        [data-testid="stExpander"] { border:1px solid #E4ECF5; border-radius:12px; background:#fff; }
        .stTabs [data-baseweb="tab-list"] { gap:4px; }
        .stTabs [data-baseweb="tab"] { border-radius:8px 8px 0 0; font-weight:700; font-size:.82rem; }
        .stTabs [aria-selected="true"] { background:#F4B400 !important; color:#17263A !important; }
        div[data-testid="stDataFrame"] { border:1px solid #E4ECF5; border-radius:12px; overflow:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=4, show_spinner=False)
def mcp_health() -> dict:
    try:
        response = requests.get(MCP_HEALTH, timeout=0.9)
        response.raise_for_status()
        return {"online": True, **response.json()}
    except Exception:
        return {"online": False, "tools": [t["name"] for t in core.list_tools()]}


@st.cache_data(ttl=4, show_spinner=False)
def a2a_health() -> dict:
    try:
        response = requests.get(A2A_HEALTH, timeout=0.9)
        response.raise_for_status()
        return {"online": True, **response.json()}
    except Exception:
        return {"online": False, "agent": "orchestrateur"}


@st.cache_data(ttl=15, show_spinner=False)
def cached_stats(segment: str) -> dict:
    return core.learning_statistics(segment)


@st.cache_data(ttl=30, show_spinner=False)
def cached_learners() -> list[dict]:
    return core.learners()


@st.cache_data(ttl=30, show_spinner=False)
def cached_courses() -> list[dict]:
    return core.courses()


def esc(value: object) -> str:
    return html.escape(str(value))


def compact_html(value: str) -> str:
    """Supprime l'indentation : Markdown interprète 4 espaces comme un bloc de code."""
    return "".join(line.strip() for line in value.splitlines())


def md_html(value: str) -> str:
    """Rend le Markdown généré par les agents dans une carte HTML stylée."""
    return mistune.html(value)


def hero(kicker: str, title: str, subtitle: str, chips: list[tuple[str, str]] | None = None) -> None:
    chips_html = ""
    if chips:
        chips_html = "<div class='chips'>" + "".join(
            f"<span class='chip {css}'>{esc(label)}</span>" for label, css in chips
        ) + "</div>"
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">{esc(kicker)}</div>
            <h1>{esc(title)}</h1>
            <p>{esc(subtitle)}</p>
            {chips_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric(label: str, value: str, icon: str, delta: str = "", color: str = "#EEF5FC") -> str:
    delta_html = f"<div class='delta'>{esc(delta)}</div>" if delta else ""
    return (
        f"<div class='metric'><div class='ico' style='background:{color}'>{icon}</div>"
        f"<div><div class='val'>{esc(value)}</div><div class='lab'>{esc(label)}</div>{delta_html}</div></div>"
    )


def metrics_row(items: list[tuple[str, str, str, str, str]]) -> None:
    st.markdown(
        "<div class='grid metrics'>" + "".join(metric(*item) for item in items) + "</div>",
        unsafe_allow_html=True,
    )


def status_pill(online: bool, label: str) -> str:
    cls = "status" if online else "status off"
    suffix = "en ligne" if online else "hors ligne · repli local"
    return f"<span class='{cls}'><span class='dot'></span>{esc(label)} · {suffix}</span>"


def plot_layout(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=42, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=NAVY, size=11),
        title_font=dict(size=13, color=NAVY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=10)),
        hoverlabel=dict(bgcolor="white", font_size=11, font_family="Inter"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E4ECF5")
    fig.update_yaxes(gridcolor="#EDF2F8", zeroline=False, linecolor="#E4ECF5")
    return fig


def card(title: str, body: str, tag: str = "") -> str:
    tag_html = f"<div class='tag'>{esc(tag)}</div>" if tag else ""
    return f"<div class='card'><h3>{esc(title)}</h3><p>{body}</p>{tag_html}</div>"


def file_size(path: Path) -> str:
    if not path.exists():
        return "à générer"
    size = path.stat().st_size
    if size > 1024 * 1024:
        return f"{size / (1024*1024):.1f} Mo"
    return f"{size / 1024:.0f} Ko"


def call_mcp(tool: str, arguments: dict) -> tuple[dict, float, str]:
    started = time.perf_counter()
    if mcp_health()["online"]:
        try:
            response = requests.post(MCP_TOOL, json={"tool": tool, "arguments": arguments}, timeout=8)
            response.raise_for_status()
            body = response.json()
            return body["result"], body.get("latency_ms", round((time.perf_counter() - started) * 1000, 1)), "MCP · HTTP"
        except Exception:
            pass
    handlers = {
        "search_courses": lambda: core.search_courses(
            arguments.get("query", ""), arguments.get("level") or None, arguments.get("max_results", 5)
        ),
        "get_learner_profile": lambda: core.get_learner_profile(arguments.get("learner_id", "L001")),
        "recommend_learning_path": lambda: core.recommend_learning_path(
            arguments.get("learner_id", "L001"), arguments.get("target_skill") or None
        ),
        "generate_quiz": lambda: core.generate_quiz(
            arguments.get("course_id", "PY101"), arguments.get("difficulty") or None, arguments.get("n_questions", 3)
        ),
        "grade_quiz": lambda: core.grade_quiz(
            arguments.get("learner_id", "L001"), arguments.get("course_id", "PY101"), arguments.get("answers", {})
        ),
        "get_learning_statistics": lambda: core.learning_statistics(arguments.get("segment", "Tous")),
    }
    result = handlers[tool]()
    return result, round((time.perf_counter() - started) * 1000, 1), "Local · repli"


def format_path(result: dict) -> str:
    steps = "\n".join(
        f"{step['step']}. **{step['id']} — {step['title']}** · {step['duration_h']} h · {step['level']}"
        for step in result.get("path", [])
    ) or "Aucun cours restant : le parcours est déjà validé."
    already = ""
    if result.get("already_validated"):
        already = "\n\n**Déjà validé** : " + ", ".join(c["id"] for c in result["already_validated"])
    return (
        f"### Parcours recommandé pour {result.get('learner_name','')}\n"
        f"**Objectif** : {result.get('target_skill_label','')} · **{result.get('steps',0)} étapes** · "
        f"**{result.get('total_hours',0)} h**\n\n{steps}{already}\n\n"
        f"> {result.get('message','')}"
    )


def format_quiz(quiz: dict) -> str:
    lines = [
        f"### Quiz {quiz.get('quiz_id','')} · {quiz.get('course_title','')}",
        f"**{quiz.get('question_count',0)} questions** · difficulté : {quiz.get('difficulty','Tous niveaux')}",
        "",
    ]
    for index, question in enumerate(quiz.get("questions", []), 1):
        lines.append(f"**{index}. {question['question']}**")
        lines.extend(f"   - {i}. {choice}" for i, choice in enumerate(question["choices"]))
        lines.append("")
    lines.append("> " + quiz.get("instructions", "Répondez avec l'index de la bonne réponse."))
    return "\n".join(lines)


def format_profile(profile: dict) -> str:
    completed = ", ".join(c["title"] for c in profile.get("completed_courses", [])) or "aucun cours validé"
    next_course = profile.get("recommended_next") or {}
    return (
        f"### Profil de {profile['name']}\n"
        f"**{profile['level']}** · cohorte **{profile['cohort']}** · objectif **{profile['goal']}**\n\n"
        f"- Progression : **{profile['progress_pct']} %** · engagement : **{profile['engagement']}**\n"
        f"- Moyenne quiz : **{profile['quiz_average']}/100** · tentatives : **{profile['attempts_count']}**\n"
        f"- Cours validés : {completed}\n"
        + (
            f"- Prochain cours conseillé : **{next_course.get('id')} — {next_course.get('title')}**\n"
            if next_course
            else ""
        )
    )


def format_stats(stats: dict) -> str:
    kpis = stats["kpis"]
    return (
        "### Statistiques d'apprentissage\n"
        f"- **{kpis['learners']} apprenants** · {kpis['active_learners']} actifs · {kpis['courses']} cours\n"
        f"- Score moyen : **{kpis['avg_score']}/100** · réussite quiz : **{kpis['success_rate']} %**\n"
        f"- Complétion moyenne : **{kpis['avg_completion']} %** · inscriptions : **{kpis['enrollments']:,}**\n"
        f"- Délégations A2A : **{kpis['delegations']}** · succès : **{kpis['delegation_success']} %** · "
        f"latence moyenne : **{kpis['avg_latency_ms']} ms**\n"
    )


def mcp_agent_response(
    message: str, learner_id: str, target_skill: str, course_id: str, difficulty: str
) -> tuple[str, list[dict]]:
    normalized = core.normalize(message)
    trace: list[dict] = []

    def record(tool: str, args: dict) -> dict:
        result, latency, source = call_mcp(tool, args)
        trace.append(
            {
                "tool": tool,
                "arguments": args,
                "result": result,
                "latency_ms": latency,
                "source": source,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        )
        return result

    if any(word in normalized for word in ("bonjour", "hello", "salut")) and len(normalized) < 30:
        return (
            "### Bonjour 👋\nJe suis l'agent EduAgentic connecté au serveur MCP. "
            "Je peux rechercher un cours, consulter un profil, construire un parcours, générer un quiz "
            "ou afficher les statistiques. Essayez : « Construis le parcours de Lina vers Data Analyst ».",
            trace,
        )

    wants_quiz = any(word in normalized for word in ("quiz", "évaluation", "evaluation", "question", "test"))
    wants_path = any(word in normalized for word in ("parcours", "recommand", "chemin", "roadmap", "devenir"))
    wants_profile = any(word in normalized for word in ("profil", "progression", "apprenant", "compétence", "competence"))
    wants_stats = any(word in normalized for word in ("statistique", "statistiques", "kpi", "tableau de bord", "dashboard"))

    parts: list[str] = []
    if wants_stats:
        stats = record("get_learning_statistics", {"segment": "Tous"})
        parts.append(format_stats(stats))
    elif wants_quiz and not wants_path:
        quiz = record(
            "generate_quiz",
            {"course_id": course_id, "difficulty": difficulty if difficulty != "Tous niveaux" else "", "n_questions": 3},
        )
        parts.append(format_quiz(quiz))
        parts.append("> Pour corriger vos réponses, ouvrez le formulaire de correction ou demandez « corrige mon quiz ».")
    elif wants_path or wants_profile:
        profile = record("get_learner_profile", {"learner_id": learner_id})
        parts.append(format_profile(profile))
        if wants_path or "parcours" in normalized:
            path = record("recommend_learning_path", {"learner_id": learner_id, "target_skill": target_skill})
            parts.append(format_path(path))
        resources = record("search_courses", {"query": target_skill or profile["goal"], "max_results": 4})
        if resources.get("results"):
            rows = "\n".join(
                f"- **{c['id']} · {c['title']}** — {c['level']}, {c['duration_h']} h, pertinence {int(c['relevance']*100)} %"
                for c in resources["results"][:4]
            )
            parts.append(f"### Ressources MCP\n{rows}")
    else:
        resources = record("search_courses", {"query": message, "max_results": 5})
        if resources.get("results"):
            rows = "\n".join(
                f"- **{c['id']} · {c['title']}** — {c['level']}, {c['duration_h']} h, "
                f"compétences : {', '.join(c['skills'])}, pertinence {int(c['relevance']*100)} %"
                for c in resources["results"]
            )
            parts.append(
                f"### Résultats de recherche\n{rows}\n\n"
                "> L'agent a choisi `search_courses` automatiquement ; le résultat vient du serveur MCP."
            )
        else:
            parts.append(
                "Je n'ai trouvé aucun cours correspondant. Essayez « data analyst », « quiz Python » "
                "ou « parcours machine learning »."
            )
    return "\n\n".join(parts), trace


def trace_html(trace: list[dict]) -> str:
    if not trace:
        return "<p style='color:#6B7C93'>Aucun appel d'outil.</p>"
    items = []
    for item in trace:
        items.append(
            f"""
            <div class="trace-item">
                <div class="trace-head"><b>{esc(item['tool'])}</b>
                    <span class="badge {'local' if 'Local' in item['source'] else ''}">{esc(item['source'])}</span>
                    <span class="badge">{item['latency_ms']} ms</span>
                </div>
                <div class="trace-meta">à {esc(item['timestamp'])} · arguments : {esc(json.dumps(item['arguments'], ensure_ascii=False))}</div>
            </div>
            """
        )
    return "<div class='trace'>" + compact_html("".join(items)) + "</div>"


def agent_cards_html(cards: list[dict]) -> None:
    icons = {
        "agent-tuteur": "🧑‍🏫",
        "agent-evaluation": "📝",
        "agent-orientation": "🧭",
        "orchestrateur": "🎛️",
    }
    blocks = []
    for item in cards:
        card_data = item.get("card", {})
        skills = "".join(f"<span class='skill'>{esc(s['name'])}</span>" for s in card_data.get("skills", []))
        online = item.get("status") == "en ligne"
        blocks.append(
            f"""
            <div class="agent">
                <div class="top"><div class="avatar">{icons.get(item['agent_id'],'🤖')}</div>
                    <div><div class="name">{esc(item.get('label', card_data.get('name','')))}</div>
                    <div class="port">port {a2a_core.AGENT_PORTS.get(item['agent_id'],'—')} ·
                    {'<span style="color:#0C7B67">● en ligne</span>' if online else '<span style="color:#B23B2E">● carte locale</span>'}</div></div>
                </div>
                <div class="desc">{esc(card_data.get('description',''))[:150]}</div>
                <div>{skills}</div>
            </div>
            """
        )
    st.markdown("<div class='agent-grid'>" + compact_html("".join(blocks)) + "</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
def page_home() -> None:
    hero(
        "Agentic AI in Education Technology · Jours 33 & 34",
        "Deux protocoles, une plateforme d'apprentissage augmentée",
        "MCP expose les outils EdTech à un agent. A2A fait collaborer des agents spécialisés. "
        "Le dashboard relie les deux démonstrations, les traces et les statistiques dans une interface unique.",
        [("MCP · J33", "gold"), ("A2A · J34", "teal"), ("Langflow / Playground", ""), ("localhost:8011", "")],
    )
    stats = cached_stats("Tous")
    kpis = stats["kpis"]
    metrics_row(
        [
            ("Apprenants suivis", str(kpis["learners"]), "🎓", f"{kpis['active_learners']} actifs", "#EEF5FC"),
            ("Cours au catalogue", str(kpis["courses"]), "📚", f"{kpis['enrollments']:,} inscriptions", "#FFF7E0"),
            ("Score moyen", f"{kpis['avg_score']}", "📈", f"{kpis['success_rate']} % de réussite", "#EAF8F4"),
            ("Délégations A2A", str(kpis["delegations"]), "🤝", f"{kpis['delegation_success']} % de succès", "#EEF5FC"),
            ("Latence agent", f"{int(kpis['avg_latency_ms'])} ms", "⚡", "moyenne des échanges", "#FFF7E0"),
        ]
    )
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown(
            card(
                "J33 · Serveur MCP EdTech",
                "Six outils standards exposés en SSE : recherche de cours, profil, parcours, quiz, "
                "correction et statistiques. L'agent les découvre automatiquement et choisit le bon outil.",
                "Model Context Protocol · Langflow · FastMCP",
            ),
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Ouvrir le playground MCP →", use_container_width=True, key="go_mcp"):
            st.session_state.nav = MENU[1]
            st.rerun()
    with col2:
        st.markdown(
            card(
                "J34 · Orchestration A2A",
                "Un orchestrateur découvre les AgentCards du Tuteur, de l'Évaluation et de l'Orientation, "
                "puis délègue en parallèle avec un correlation_id traçable.",
                "Agent-to-Agent · AgentCard · Discovery · Delegation",
            ),
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Lancer une orchestration A2A →", use_container_width=True, key="go_a2a"):
            st.session_state.nav = MENU[2]
            st.rerun()

    st.markdown("<div class='section-title'>Le parcours de la démonstration</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card" style="padding:18px 22px">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;align-items:start">
            <div><span class="pill">01 · Données</span><p style="margin-top:7px">Catalogue de 14 cours, 24 apprenants, 168 tentatives de quiz et 84 traces A2A synthétiques.</p></div>
            <div><span class="pill">02 · Outils MCP</span><p style="margin-top:7px">Le serveur expose 6 outils ; le playground montre l'appel, les arguments, la latence et le résultat.</p></div>
            <div><span class="pill">03 · Agents A2A</span><p style="margin-top:7px">3 AgentCards, une découverte HTTP, 3 délégations parallèles et un correlation_id unique par demande.</p></div>
            <div><span class="pill">04 · Décision</span><p style="margin-top:7px">Le dashboard agrège KPI, graphiques et traces pour vérifier la qualité et la performance.</p></div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-title' style='margin-top:22px'>Activité récente</div>", unsafe_allow_html=True)
    recent = pd.DataFrame(stats["recent_attempts"][:8])
    if not recent.empty:
        recent = recent[["attempt_date", "learner_name", "course_id", "score", "passed", "duration_min"]]
        recent.columns = ["Date", "Apprenant", "Cours", "Score", "Réussi", "Durée (min)"]
        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True,
            column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")},
        )
    st.markdown(
        "<div class='footer'><span>EduAgentic v1.0 · données synthétiques · 11 novembre 2026</span>"
        "<span>Dashboard : <b>localhost:8011</b> · MCP : 8000 · A2A : 8001</span></div>",
        unsafe_allow_html=True,
    )


def page_mcp() -> None:
    hero(
        "Jour 33 · Model Context Protocol",
        "MCP Playground : l'agent découvre et utilise les outils EdTech",
        "Posez une question en langage naturel. L'agent sélectionne un outil MCP, l'exécute et affiche "
        "la trace complète (outil, arguments, latence, résultat).",
        [("Serveur SSE", "gold"), ("6 outils", ""), ("Playground", "teal")],
    )
    health = mcp_health()
    online = health["online"]
    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        st.markdown(status_pill(online, "Serveur MCP 127.0.0.1:8000"), unsafe_allow_html=True)
    with col2:
        st.markdown(f"<span class='pill'>Transport SSE · /sse</span>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<span class='pill'>{len(health.get('tools', []))} outils exposés</span>", unsafe_allow_html=True)
    st.write("")

    tools = core.list_tools()
    st.markdown(
        "<div style='display:flex;gap:6px;flex-wrap:wrap;margin:2px 0 14px'>"
        + "".join(f"<span class='skill' style='font-size:.7rem;padding:5px 9px'>{esc(t['name'])}</span>" for t in tools)
        + "</div>",
        unsafe_allow_html=True,
    )

    with st.form("mcp_form"):
        st.markdown("<div class='section-title' style='font-size:.98rem;margin-top:0'>Configurer le contexte</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
        learners = cached_learners()
        learner_labels = [f"{l['id']} · {l['name']}" for l in learners]
        with c1:
            learner_choice = st.selectbox("Apprenant", learner_labels, index=0)
        learner_id = learner_choice.split(" · ")[0]
        with c2:
            skill_keys = list(core.SKILL_LABELS.keys())
            target_skill = st.selectbox(
                "Compétence cible",
                skill_keys,
                index=skill_keys.index("data-analysis"),
                format_func=core.skill_label,
            )
        with c3:
            course_ids = [c["id"] for c in cached_courses()]
            course_id = st.selectbox("Cours (quiz)", course_ids, index=0)
        with c4:
            difficulty = st.selectbox("Difficulté", ["Tous niveaux", "facile", "moyen", "difficile"])
        default_message = st.session_state.get("mcp_message", "Construis le parcours de Lina vers Data Analyst")
        message = st.text_area(
            "Message à l'agent",
            value=default_message,
            height=82,
            placeholder="Ex. : Quels cours pour devenir Data Analyst ? Génère aussi un quiz Python.",
        )
        submitted = st.form_submit_button("▶  Exécuter dans le playground MCP", use_container_width=True)

    q1, q2, q3 = st.columns(3)
    if q1.button("Exemple : parcours Data Analyst", use_container_width=True):
        st.session_state.mcp_message = "Construis le parcours de Lina vers Data Analyst"
        st.rerun()
    if q2.button("Exemple : quiz Python", use_container_width=True):
        st.session_state.mcp_message = "Génère un quiz Python de niveau facile"
        st.session_state.mcp_course = "PY101"
        st.rerun()
    if q3.button("Exemple : statistiques", use_container_width=True):
        st.session_state.mcp_message = "Montre-moi les statistiques d'apprentissage"
        st.rerun()

    if submitted and message.strip():
        with st.spinner("L'agent interroge le serveur MCP…"):
            answer, trace = mcp_agent_response(message, learner_id, target_skill, course_id, difficulty)
        st.session_state.mcp_history = (
            [{"role": "assistant", "content": answer, "trace": trace, "time": datetime.now().strftime("%H:%M:%S")}]
            + st.session_state.get("mcp_history", [])
        )[:6]

    history = st.session_state.get("mcp_history", [])
    if not history:
        st.info("Choisissez un exemple ou posez votre question : le playground appellera réellement le serveur MCP si celui-ci est lancé.")
    for item in history:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin:14px 0 6px'>"
            f"<span class='badge'>MCP · {esc(item['time'])}</span>"
            f"<span style='font-size:.74rem;color:#6B7C93'>agent → serveur → outil → réponse</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='answer'>{md_html(item['content'])}</div>", unsafe_allow_html=True)
        with st.expander(f"Trace d'exécution · {len(item['trace'])} outil(s) · cliquez pour inspecter", expanded=False):
            st.markdown(trace_html(item["trace"]), unsafe_allow_html=True)
            for index, call in enumerate(item["trace"], 1):
                st.markdown(f"**{index}. `{call['tool']}`** — {call['source']} · {call['latency_ms']} ms")
                st.code(json.dumps(call["result"], ensure_ascii=False, indent=2)[:2600], language="json")

    st.markdown(
        "<div class='footer'><span>MCP 1.x · FastMCP · SSE <code>/sse</code> · 6 outils</span>"
        "<span>Si le serveur est arrêté, le playground bascule sur le moteur local et l'indique dans la trace.</span></div>",
        unsafe_allow_html=True,
    )


def page_a2a() -> None:
    hero(
        "Jour 34 · Agent-to-Agent",
        "A2A Orchestration : découvrir, déléguer, tracer",
        "L'orchestrateur interroge les AgentCards, choisit les spécialistes et consolide leurs réponses. "
        "Chaque échange porte un correlation_id unique, visible dans la timeline et les logs.",
        [("AgentCard", "teal"), ("Discovery", ""), ("Delegation", "gold"), ("correlation_id", "")],
    )
    online = a2a_health()["online"]
    c1, c2, c3, c4 = st.columns([1.3, 1, 1, 1])
    with c1:
        st.markdown(status_pill(online, "Orchestrateur A2A 127.0.0.1:8001"), unsafe_allow_html=True)
    with c2:
        st.markdown("<span class='pill'>A2A 0.3.0</span>", unsafe_allow_html=True)
    with c3:
        st.markdown("<span class='pill'>JSON-RPC 2.0</span>", unsafe_allow_html=True)
    with c4:
        st.markdown("<span class='pill'>3 agents · 1 orchestrateur</span>", unsafe_allow_html=True)

    st.markdown("<div class='section-title' style='margin-top:18px'>Découverte des agents</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-sub'>Chaque agent publie sa carte sur <code>/.well-known/agent.json</code> ; "
        "l'orchestrateur la lit avant toute délégation.</div>",
        unsafe_allow_html=True,
    )
    try:
        if online:
            response = requests.get(A2A_DISCOVER, timeout=3)
            cards = response.json()["agents"]
        else:
            raise RuntimeError("offline")
    except Exception:
        cards = a2a_core.discover_agents(use_network=False)
    agent_cards_html(cards)

    with st.form("a2a_form"):
        st.markdown("<div class='section-title' style='font-size:.98rem;margin-top:4px'>Demande d'apprentissage</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1.2, 1, 1])
        learners = cached_learners()
        labels = [f"{l['id']} · {l['name']}" for l in learners]
        with col1:
            learner_choice = st.selectbox("Apprenant", labels, index=0, key="a2a_learner")
        learner_id = learner_choice.split(" · ")[0]
        with col2:
            objectives = [
                "Devenir Data Analyst",
                "Devenir Data Scientist",
                "Devenir ML Engineer",
                "Devenir enseignante augmentée par l'IA",
                "Se reconvertir dans la data",
            ]
            objective = st.selectbox("Objectif", objectives, index=0)
        with col3:
            skill_keys = list(core.SKILL_LABELS.keys())
            target_skill = st.selectbox(
                "Compétence cible",
                skill_keys,
                index=skill_keys.index("data-analysis"),
                format_func=core.skill_label,
                key="a2a_skill",
            )
        question = st.text_area(
            "Question / tâche à déléguer",
            value="Je veux un parcours, des ressources et un quiz pour progresser.",
            height=76,
        )
        local_mode = st.checkbox("Forcer le mode local (sans serveurs A2A)", value=not online)
        submitted = st.form_submit_button("▶  Orchestrer la demande A2A", use_container_width=True)

    if submitted:
        payload = {
            "learner_id": learner_id,
            "objective": objective,
            "question": question,
            "target_skill": target_skill,
            "use_network": not local_mode,
        }
        with st.spinner("Découverte des AgentCards, puis délégation parallèle…"):
            result = None
            try:
                if online and not local_mode:
                    response = requests.post(A2A_ORCHESTRATE, json=payload, timeout=25)
                    response.raise_for_status()
                    result = response.json()["result"]
                else:
                    raise RuntimeError("mode local")
            except Exception:
                result = a2a_core.orchestrate_request(
                    learner_id=learner_id,
                    objective=objective,
                    question=question,
                    target_skill=target_skill,
                    use_network=False,
                )
        st.session_state.a2a_result = result

    result = st.session_state.get("a2a_result")
    if not result:
        st.info("Lancez une orchestration : elle appellera réellement les agents Tuteur, Évaluation et Orientation si les services sont démarrés.")
        st.markdown(
            "<div class='footer'><span>AgentCards : port 8101, 8102, 8103 · Orchestrateur : 8001</span>"
            "<span>Sans serveur, le dashboard utilise exactement les mêmes handlers en local.</span></div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown("<div class='section-title' style='margin-top:22px'>Résultat de l'orchestration</div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(metric("Correlation ID", result["correlation_id"], "🔗", "trace unique", "#EEF5FC"), unsafe_allow_html=True)
    k2.markdown(metric("Agents", str(len(result["delegations"])), "🤖", "spécialistes", "#EAF8F4"), unsafe_allow_html=True)
    k3.markdown(metric("Latence totale", f"{int(result['total_latency_ms'])} ms", "⚡", "orchestration", "#FFF7E0"), unsafe_allow_html=True)
    k4.markdown(metric("Protocole", "A2A 0.3", "📡", "JSON-RPC 2.0", "#EEF5FC"), unsafe_allow_html=True)
    st.write("")

    tab_answer, tab_trace, tab_cards, tab_logs = st.tabs(
        ["💬 Réponse consolidée", "🧭 Timeline de délégation", "🪪 AgentCards", "🗂️ Logs récents"]
    )
    with tab_answer:
        st.markdown(f"<div class='answer'>{md_html(result['answer'])}</div>", unsafe_allow_html=True)
        st.caption(
            f"Demande : « {result['question']} » · corrélation : {result['correlation_id']} · "
            f"{result['protocol']['version']}"
        )
    with tab_trace:
        for delegation in result["delegations"]:
            status = delegation["status"]
            badge_cls = "badge failed" if "failed" in status else "badge local" if "local" in delegation["transport"] else "badge"
            items = (
                f"<div class='trace-item {'failed' if 'failed' in status else ''}'>"
                f"<div class='trace-head'><b>orchestrateur → {esc(delegation['label'])}</b>"
                f"<span class='{badge_cls}'>{esc(status)}</span>"
                f"<span class='badge'>{esc(delegation['transport'])}</span>"
                f"<span class='badge'>{delegation['latency_ms']} ms</span></div>"
                f"<div class='trace-meta'>{esc(delegation['result'].get('summary',''))}</div></div>"
            )
            st.markdown("<div class='trace'>" + compact_html(items) + "</div>", unsafe_allow_html=True)
            with st.expander(f"Inspecter la tâche déléguée · {delegation['agent_id']}"):
                st.markdown("**Payload envoyé**")
                st.code(json.dumps(delegation["payload"], ensure_ascii=False, indent=2)[:1800], language="json")
                st.markdown("**Résultat de l'agent**")
                st.code(json.dumps(delegation["result"], ensure_ascii=False, indent=2)[:3200], language="json")
        with st.expander("Trace JSON complète (artifacts, découverte, protocole)"):
            st.code(json.dumps(result, ensure_ascii=False, indent=2)[:12000], language="json")
    with tab_cards:
        agent_cards_html(result["agents_discovered"])
    with tab_logs:
        logs = a2a_core.recent_traces(10)
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune trace persistée pour le moment.")

    st.markdown(
        "<div class='footer'><span>Chaque délégation est écrite dans <code>data/a2a_live.jsonl</code>.</span>"
        "<span>Le correlation_id relie les 3 échanges à la demande initiale.</span></div>",
        unsafe_allow_html=True,
    )


def page_stats() -> None:
    hero(
        "Statistiques & pilotage",
        "Ce que disent les données d'apprentissage",
        "Vue agrégée des apprenants, des quiz et des délégations A2A. Les filtres se recalculent en direct "
        "sur le jeu de données synthétique.",
        [("KPI", "gold"), ("Graphiques", ""), ("Export CSV", "teal")],
    )
    cohorts = ["Tous"] + sorted({l["cohort"] for l in cached_learners()})
    c1, c2 = st.columns([2, 1])
    with c1:
        segment = st.selectbox("Filtrer par cohorte", cohorts, index=0)
    with c2:
        st.caption("Données : 15 sept. → 10 nov. 2026 · 168 tentatives · 84 traces A2A")
    stats = cached_stats(segment)
    kpis = stats["kpis"]
    metrics_row(
        [
            ("Apprenants", str(kpis["learners"]), "🎓", segment, "#EEF5FC"),
            ("Score moyen", f"{kpis['avg_score']}", "📈", f"{kpis['attempts']} tentatives", "#EAF8F4"),
            ("Réussite quiz", f"{kpis['success_rate']} %", "✅", "seuil 70/100", "#FFF7E0"),
            ("Complétion", f"{kpis['avg_completion']} %", "🎯", "moyenne des cours", "#EEF5FC"),
            ("Succès A2A", f"{kpis['delegation_success']} %", "🤝", f"{kpis['avg_latency_ms']} ms", "#EAF8F4"),
        ]
    )
    st.write("")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        weekly = pd.DataFrame(stats["score_by_week"])
        fig = px.line(
            weekly,
            x="week",
            y="avg_score",
            markers=True,
            title="Évolution du score moyen par semaine",
            labels={"week": "Semaine", "avg_score": "Score moyen"},
        )
        fig.update_traces(line=dict(color=GOLD, width=3), marker=dict(size=7, color=NAVY))
        fig.add_hline(y=70, line_dash="dot", line_color=TEAL, annotation_text="Seuil de réussite")
        fig.update_yaxes(range=[40, 100])
        st.plotly_chart(plot_layout(fig), use_container_width=True, config={"displayModeBar": False})
    with col2:
        levels = pd.DataFrame(stats["by_level"])
        fig = px.bar(
            levels,
            x="level",
            y="count",
            title="Apprenants par niveau",
            color="level",
            color_discrete_sequence=PALETTE,
            text="count",
            labels={"level": "Niveau", "count": "Apprenants"},
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(showlegend=False)
        st.plotly_chart(plot_layout(fig), use_container_width=True, config={"displayModeBar": False})

    col3, col4 = st.columns(2, gap="large")
    with col3:
        domains = pd.DataFrame(stats["enrollment_by_domain"])
        fig = px.pie(
            domains,
            names="domain",
            values="enrolled",
            hole=0.58,
            title="Répartition des inscriptions par domaine",
            color_discrete_sequence=PALETTE,
        )
        fig.update_traces(textinfo="percent", textfont_size=10)
        fig = plot_layout(fig, height=340)
        fig.update_layout(
            legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center", font=dict(size=9)),
            margin=dict(l=8, r=8, t=42, b=68),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col4:
        completion = pd.DataFrame(stats["completion_by_course"]).head(8)
        fig = px.bar(
            completion.sort_values("completion_rate"),
            x="completion_rate",
            y="title",
            orientation="h",
            title="Taux de complétion par cours",
            color="completion_rate",
            color_continuous_scale=["#DCE8F4", TEAL, NAVY],
            text="completion_rate",
            labels={"completion_rate": "Taux de complétion (%)", "title": "Cours"},
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, showlegend=False)
        fig.update_yaxes(automargin=True, tickfont=dict(size=9))
        fig.update_xaxes(range=[0, 100])
        fig = plot_layout(fig, height=360)
        fig.update_layout(margin=dict(l=250, r=24, t=42, b=12))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    col5, col6 = st.columns(2, gap="large")
    with col5:
        distribution = pd.DataFrame(stats["score_distribution"])
        fig = px.bar(
            distribution,
            x="range",
            y="count",
            title="Distribution des scores",
            color="count",
            color_continuous_scale=["#DCE8F4", BLUE, NAVY],
            text="count",
            labels={"range": "Tranche de score", "count": "Tentatives"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, showlegend=False)
        st.plotly_chart(plot_layout(fig), use_container_width=True, config={"displayModeBar": False})
    with col6:
        delegations = pd.DataFrame(stats["delegation_by_agent"])
        fig = go.Figure()
        fig.add_bar(
            x=delegations["agent"],
            y=delegations["delegations"],
            name="Délégations",
            marker_color=[TEAL, GOLD, BLUE],
            text=delegations["delegations"],
            textposition="outside",
        )
        fig.add_trace(
            go.Scatter(
                x=delegations["agent"],
                y=delegations["success_rate"],
                name="Taux de succès (%)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color=NAVY, width=2),
                marker=dict(size=8),
            )
        )
        fig = plot_layout(fig, height=340)
        fig.update_layout(
            title="Délégations A2A par agent",
            yaxis=dict(title="Délégations"),
            yaxis2=dict(title="Succès (%)", overlaying="y", side="right", range=[0, 100], dtick=25, showgrid=False),
            legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=9)),
            margin=dict(l=8, r=8, t=52, b=55),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='section-title' style='margin-top:10px'>Dernières tentatives</div>", unsafe_allow_html=True)
    recent = pd.DataFrame(stats["recent_attempts"])
    if not recent.empty:
        recent = recent[["attempt_date", "learner_name", "course_id", "score", "passed", "duration_min"]]
        recent.columns = ["Date", "Apprenant", "Cours", "Score", "Réussi", "Durée (min)"]
        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True,
            column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")},
        )
        st.download_button(
            "⬇️  Exporter ces données en CSV",
            data=recent.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"edtech_statistiques_{segment.replace(' ', '_')}.csv",
            mime="text/csv",
        )
    st.markdown(
        "<div class='footer'><span>Source : data/quiz_attempts.csv · data/a2a_delegations.csv</span>"
        "<span>Les KPI sont recalculés à partir des données brutes, pas saisis manuellement.</span></div>",
        unsafe_allow_html=True,
    )


def page_docs() -> None:
    hero(
        "Livrables",
        "Documentation, présentations, JSON et vidéos",
        "Tous les fichiers sont générés à partir du même jeu de données et des mêmes workflows. "
        "Téléchargez-les directement depuis le dashboard.",
        [("DOCX / PDF", "gold"), ("PPTX", ""), ("MP4", "teal"), ("GitHub", "")],
    )
    groups = [
        (
            "📄 Documentation",
            [
                ("Documentation J33 · MCP", DOCS / "Documentation_J33_MCP_EdTech.docx", "Word"),
                ("Documentation J33 · MCP (PDF)", DOCS / "Documentation_J33_MCP_EdTech.pdf", "PDF"),
                ("Documentation J34 · A2A", DOCS / "Documentation_J34_A2A_EdTech.docx", "Word"),
                ("Documentation J34 · A2A (PDF)", DOCS / "Documentation_J34_A2A_EdTech.pdf", "PDF"),
                ("Documentation globale J33 + J34", DOCS / "Documentation_Globale_J33_J34.docx", "Word"),
                ("Documentation globale (PDF)", DOCS / "Documentation_Globale_J33_J34.pdf", "PDF"),
            ],
        ),
        (
            "📊 Présentations",
            [
                ("Présentation J33 · MCP", PRESENTATION / "J33_MCP_Presentation.pptx", "PowerPoint"),
                ("Présentation J33 · MCP (PDF)", PRESENTATION / "J33_MCP_Presentation.pdf", "PDF"),
                ("Présentation J34 · A2A", PRESENTATION / "J34_A2A_Presentation.pptx", "PowerPoint"),
                ("Présentation J34 · A2A (PDF)", PRESENTATION / "J34_A2A_Presentation.pdf", "PDF"),
                ("Présentation finale J33 + J34", PRESENTATION / "Presentation_Finale_J33_J34.pptx", "PowerPoint"),
                ("Présentation finale (PDF)", PRESENTATION / "Presentation_Finale_J33_J34.pdf", "PDF"),
            ],
        ),
        (
            "🧩 JSON & workflows",
            [
                ("Workflow MCP final (Langflow)", JSON_DIR / "Agentic_AI_EdTech_J33_MCP_Final.json", "JSON"),
                ("Workflow A2A final (Langflow)", JSON_DIR / "Agentic_AI_EdTech_J34_A2A_Final.json", "JSON"),
                ("Registre des AgentCards", JSON_DIR / "a2a_registry.json", "JSON"),
            ],
        ),
        (
            "🎬 Vidéos",
            [
                ("Workflow MCP + Playground", VIDEOS / "J33_MCP_Workflow_Playground.mp4", "MP4"),
                ("Workflow A2A + Playground", VIDEOS / "J34_A2A_Workflow_Playground.mp4", "MP4"),
                ("Vidéo finale J33 + J34", VIDEOS / "Video_Finale_Agentic_AI_EdTech.mp4", "MP4"),
            ],
        ),
    ]
    for title, rows in groups:
        st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
        for label, path, kind in rows:
            col1, col2, col3 = st.columns([3.2, 1, 1.2])
            with col1:
                st.markdown(
                    f"<div class='doc-row'><div><div class='doc-name'>{esc(label)}</div>"
                    f"<div class='doc-meta'>{esc(path.relative_to(ROOT))}</div></div></div>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(f"<span class='pill'>{esc(kind)}</span>", unsafe_allow_html=True)
                st.caption(file_size(path))
            with col3:
                if path.exists():
                    st.download_button(
                        "Télécharger",
                        data=path.read_bytes(),
                        file_name=path.name,
                        mime="application/octet-stream",
                        key=f"dl_{path.name}",
                        use_container_width=True,
                    )
                else:
                    st.caption("À générer")
    st.markdown(
        "<div class='footer'><span>Les fichiers sont aussi disponibles dans le dépôt GitHub et le zip final.</span>"
        "<span>Version 1.0 · 11 novembre 2026</span></div>",
        unsafe_allow_html=True,
    )


def page_architecture() -> None:
    hero(
        "Architecture",
        "Deux protocoles complémentaires",
        "MCP standardise l'accès aux outils. A2A standardise la collaboration entre agents. "
        "Le dashboard est le point d'observation des deux.",
        [("MCP", "gold"), ("A2A", "teal"), ("Dashboard", ""), ("Traçabilité", "")],
    )
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### 1 · MCP — exposer des outils")
        st.markdown(
            """
            - **Serveur** : FastMCP sur `127.0.0.1:8000`, transport **SSE** (`/sse`).
            - **Client** : agent Langflow (ou playground du dashboard).
            - **Découverte** : `list_tools` puis sélection automatique selon la demande.
            - **Outils** : `search_courses`, `get_learner_profile`, `recommend_learning_path`,
              `generate_quiz`, `grade_quiz`, `get_learning_statistics`.
            - **Pont REST** : `/api/health`, `/api/tools`, `/api/tool` pour le dashboard.
            """
        )
        if (ASSETS / "architecture_mcp.png").exists():
            st.image(str(ASSETS / "architecture_mcp.png"), use_container_width=True)
        st.code(
            "chat input → agent → MCP Tools → serveur SSE :8000 → outil → réponse",
            language="text",
        )
    with col2:
        st.markdown("### 2 · A2A — faire collaborer des agents")
        st.markdown(
            """
            - **AgentCards** : `/.well-known/agent.json` sur les ports 8101, 8102, 8103.
            - **Découverte** : l'orchestrateur lit les cartes et choisit les spécialistes.
            - **Délégation** : JSON-RPC 2.0 `message/send` avec `correlation_id`.
            - **Agents** : Tuteur (cours/parcours), Évaluation (quiz/feedback), Orientation (gap/carrière).
            - **Traçabilité** : `data/a2a_live.jsonl` + timeline du dashboard.
            """
        )
        if (ASSETS / "architecture_a2a.png").exists():
            st.image(str(ASSETS / "architecture_a2a.png"), use_container_width=True)
        st.code(
            "orchestrateur → discovery → 3 délégations parallèles → agrégation → réponse",
            language="text",
        )

    st.markdown("### Tableau comparatif")
    comparison = pd.DataFrame(
        [
            ("Rôle", "Exposer des outils à un agent", "Faire collaborer des agents entre eux"),
            ("Découverte", "Liste d'outils MCP", "AgentCards + capacités"),
            ("Contrat", "Schéma d'outil (JSON Schema)", "JSON-RPC 2.0 + tâches"),
            ("Traçabilité", "Appels d'outils + latence", "correlation_id + délégations"),
            ("Dans ce projet", "J33 · serveur EdTech", "J34 · Tuteur / Évaluation / Orientation"),
        ],
        columns=["Critère", "MCP", "A2A"],
    )
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    st.markdown(
        "<div class='footer'><span>MCP : 8000 · A2A : 8001 · Agents : 8101-8103 · Dashboard : 8011</span>"
        "<span>Les deux protocoles sont indépendants et peuvent être utilisés séparément.</span></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Sidebar & routing
# --------------------------------------------------------------------------- #
def sidebar() -> str:
    with st.sidebar:
        if (ASSETS / "logo_sidebar.png").exists():
            st.image(str(ASSETS / "logo_sidebar.png"), use_container_width=True)
        elif (ASSETS / "logo.png").exists():
            st.image(str(ASSETS / "logo.png"), use_container_width=True)
        else:
            st.markdown("## 🎓 EduAgentic")
        st.markdown(
            "<div style='font-size:.72rem;line-height:1.45;color:#B9CCE0;margin:4px 0 14px'>"
            "Agentic AI in Education Technology<br>"
            "<b style='color:#F4B400'>J33 · MCP</b> &nbsp;·&nbsp; <b style='color:#8FE3DF'>J34 · A2A</b>"
            "</div>",
            unsafe_allow_html=True,
        )
        if "nav" not in st.session_state:
            st.session_state.nav = MENU[0]
        page = st.radio("Navigation", MENU, key="nav", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        mcp = mcp_health()
        a2a = a2a_health()
        storage = mcp.get("storage", {}) if mcp.get("online") else {}
        backend = "MongoDB Atlas" if storage.get("mongo") else "JSON local"
        st.markdown(
            f"<div style='background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);"
            f"border-radius:12px;padding:11px 12px;font-size:.72rem;line-height:1.7'>"
            f"<b style='color:#F4B400'>État des services</b><br>"
            f"{'🟢' if mcp['online'] else '🟠'} MCP :8000 · {'en ligne' if mcp['online'] else 'repli local'}<br>"
            f"{'🟢' if a2a['online'] else '🟠'} A2A :8001 · {'en ligne' if a2a['online'] else 'repli local'}<br>"
            f"🗄️ Données : {backend}<br>"
            f"🖥️ Dashboard :8011</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.67rem;color:#8FA6BE;line-height:1.5'>"
            "Données synthétiques · aucun apprenant réel<br>"
            "Version 1.0 · 11/11/2026<br>"
            "Kamal El Afoui</div>",
            unsafe_allow_html=True,
        )
    return page


def main() -> None:
    inject_css()
    page = sidebar()
    if page == MENU[0]:
        page_home()
    elif page == MENU[1]:
        page_mcp()
    elif page == MENU[2]:
        page_a2a()
    elif page == MENU[3]:
        page_stats()
    elif page == MENU[4]:
        page_docs()
    else:
        page_architecture()


if __name__ == "__main__":
    main()
