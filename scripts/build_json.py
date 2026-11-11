# -*- coding: utf-8 -*-
"""Construit les JSON finaux Langflow MCP/A2A et le registre des AgentCards."""
from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared import a2a_core  # noqa: E402

JSON_DIR = ROOT / "json"
JSON_DIR.mkdir(exist_ok=True)
(JSON_DIR / "agent_cards").mkdir(exist_ok=True)
SOURCE_MCP = Path(r"C:\Users\HP\Downloads\Semaine 7\Projet_jour33\j33_MCP.json")


def build_mcp() -> Path:
    data = json.loads(SOURCE_MCP.read_text(encoding="utf-8"))
    data["name"] = "Agentic_AI_EdTech_J33_MCP_Final"
    data["description"] = (
        "Agent Langflow connecté au serveur MCP EduAgentic : 6 outils EdTech "
        "(cours, profil, parcours, quiz, correction, statistiques), transport SSE."
    )
    data["tags"] = ["edtech", "mcp", "langflow", "j33", "mongodb", "fastmcp"]
    data["last_tested_version"] = "1.7.0"
    nodes = data["data"]["nodes"]
    for node in nodes:
        node_data = node.get("data", {})
        node_type = node_data.get("type")
        template = node_data.get("node", {}).get("template", {})
        if node_type == "Agent":
            if "system_prompt" in template:
                template["system_prompt"]["value"] = (
                    "Tu es un conseiller pédagogique de la plateforme EduAgentic. "
                    "Tu disposes d'outils MCP pour chercher des cours, lire un profil apprenant, "
                    "construire un parcours, générer un quiz, corriger des réponses et calculer des statistiques.\n\n"
                    "Règles :\n"
                    "- Utilise toujours un outil avant d'inventer une réponse.\n"
                    "- Ne montre jamais le JSON brut : reformule en français, avec des listes claires.\n"
                    "- Cite les identifiants de cours (PY101, SQL201, STAT210, DATA350...) et les prérequis.\n"
                    "- Adapte le niveau et le volume de la réponse au profil de l'apprenant.\n"
                    "- Si une information manque, dis-le et propose une prochaine étape.\n"
                    "- Rappelle que les données sont synthétiques et que la décision finale reste humaine."
                )
            if "agent_description" in template:
                template["agent_description"]["value"] = (
                    "Conseiller EdTech connecté au serveur MCP EduAgentic (6 outils)."
                )
            if "max_iterations" in template:
                template["max_iterations"]["value"] = 15
            if "temperature" in template:
                template["temperature"]["value"] = 0.1
        elif node_type == "MCPTools":
            if "mcp_server" in template:
                template["mcp_server"]["value"] = {
                    "config": {"url": "http://127.0.0.1:8000/sse", "transport": "sse"},
                    "name": "edumcp-edtech",
                }
        elif node_type == "note":
            node_data["node"]["description"] = (
                "# Serveur MCP EduAgentic · J33\n\n"
                "## Objectif\n\n"
                "Ce workflow connecte un agent Langflow à un serveur **MCP EdTech** qui expose six outils "
                "pédagogiques. L'agent découvre les outils, choisit celui qui répond à la demande et reçoit "
                "un résultat structuré. Le JSON brut est reformulé en français.\n\n"
                "## Architecture\n\n"
                "**Chat Input → Agent → MCP Tools → MongoDB / données EdTech → Chat Output**\n\n"
                "## Connexion MCP\n\n"
                "- Serveur : `edumcp-edtech`\n"
                "- Transport : `SSE`\n"
                "- URL locale : `http://127.0.0.1:8000/sse`\n"
                "- Option tunnel : `ngrok http 8000`, puis `https://<tunnel>/sse`\n\n"
                "Le composant **MCP Tools** doit être connecté à l'entrée **Tools** de l'Agent. "
                "Le serveur doit rester actif pendant l'utilisation du Playground.\n\n"
                "## Outils exposés\n\n"
                "`search_courses`, `get_learner_profile`, `recommend_learning_path`, "
                "`generate_quiz`, `grade_quiz`, `get_learning_statistics`.\n\n"
                "## Données\n\n"
                "Backend optionnel **MongoDB Atlas** : collections `edtech_courses`, `edtech_learners`, "
                "`edtech_quiz_bank`, `edtech_quiz_attempts`, `edtech_a2a_delegations`. "
                "Sans `MONGODB_URI`, le serveur bascule sur les fichiers JSON/CSV synthétiques.\n\n"
                "## Requêtes de démonstration\n\n"
                "1. « Construis le parcours de Lina vers Data Analyst »\n"
                "2. « Génère un quiz Python de niveau facile »\n"
                "3. « Montre-moi les statistiques d'apprentissage »\n"
            )
    # note supplémentaire sur MongoDB
    note = {
        "data": {
            "id": "note-MongoDB-J33",
            "node": {
                "description": (
                    "## Backend MongoDB Atlas (optionnel)\n\n"
                    "Renseigner `.env` :\n\n"
                    "```\nMONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/fusion\n"
                    "MONGODB_DB=fusion\nMONGODB_COLLECTION_PREFIX=edtech_\nEDTECH_BACKEND=mongo\n```\n\n"
                    "Les collections `edtech_*` sont créées et peuplées automatiquement au premier appel. "
                    "Les collections existantes ne sont jamais modifiées. Sans connexion, repli JSON automatique."
                ),
                "display_name": "",
                "documentation": "",
                "template": {},
            },
            "type": "note",
        },
        "id": "note-MongoDB-J33",
        "position": {"x": -70, "y": -260},
        "type": "note",
    }
    nodes.append(note)
    data["data"]["viewport"] = {"x": -63, "y": 12, "zoom": 0.52}
    path = JSON_DIR / "Agentic_AI_EdTech_J33_MCP_Final.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _input_field(name: str, input_type: str, display: str, value: str = "", input_types=None, field_type="str"):
    return {
        "_input_type": input_type,
        "advanced": False,
        "display_name": display,
        "dynamic": False,
        "info": "",
        "input_types": input_types or [],
        "list": False,
        "load_from_db": False,
        "name": name,
        "override_skip": False,
        "password": False,
        "placeholder": "",
        "required": False,
        "show": True,
        "title_case": False,
        "trace_as_metadata": True,
        "track_in_telemetry": False,
        "type": field_type,
        "value": value,
    }


def _code_field(code: str):
    return {
        "advanced": True,
        "dynamic": True,
        "fileTypes": [],
        "file_path": "",
        "info": "",
        "list": False,
        "load_from_db": False,
        "multiline": True,
        "name": "code",
        "password": False,
        "placeholder": "",
        "required": True,
        "show": True,
        "title_case": False,
        "type": "code",
        "value": code,
    }


A2A_CODE = '''from lfx.custom.custom_component.component import Component
from lfx.io import MessageInput, StrInput, Output
from lfx.schema.message import Message

import json
import requests


class A2AOrchestrator(Component):
    display_name = "Orchestrateur A2A EduAgentic"
    description = (
        "Découvre les AgentCards, délègue la demande aux agents Tuteur, Évaluation et "
        "Orientation, puis agrège la réponse et le correlation_id."
    )
    icon = "network"

    inputs = [
        MessageInput(name="question", display_name="Question / tâche", info="Demande de l'utilisateur"),
        StrInput(name="learner_id", display_name="Apprenant", value="L001"),
        StrInput(name="objective", display_name="Objectif", value="Devenir Data Analyst"),
        StrInput(name="target_skill", display_name="Compétence cible", value="data-analysis"),
        StrInput(
            name="orchestrator_url",
            display_name="URL de l'orchestrateur",
            value="http://127.0.0.1:8001/orchestrate",
        ),
    ]
    outputs = [
        Output(name="response", display_name="Réponse A2A", method="run_orchestration"),
    ]

    def run_orchestration(self) -> Message:
        payload = {
            "learner_id": self.learner_id or "L001",
            "objective": self.objective or "Devenir Data Analyst",
            "target_skill": self.target_skill or "data-analysis",
            "question": self.question.text if hasattr(self.question, "text") else str(self.question),
        }
        try:
            response = requests.post(self.orchestrator_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()["result"]
        except Exception as exc:
            return Message(
                text=(
                    "L'orchestrateur A2A n'est pas joignable. "
                    "Lancez `python a2a/run_all.py`, puis réessayez.\\n\\n"
                    f"Détail : {exc}"
                )
            )
        lines = [
            f"### Réponse A2A · {data['correlation_id']}",
            "",
            data["answer"],
            "",
            "### Délégations",
        ]
        for item in data["delegations"]:
            lines.append(
                f"- **{item['label']}** · {item['status']} · {item['transport']} · {item['latency_ms']} ms"
            )
        lines.append("")
        lines.append(f"Latence totale : {data['total_latency_ms']} ms")
        return Message(text="\\n".join(lines))
'''


def build_a2a() -> Path:
    # Reprend les noeuds ChatInput / ChatOutput du modèle J33 pour rester compatible Langflow 1.7.
    base = json.loads(SOURCE_MCP.read_text(encoding="utf-8"))
    chat_input = None
    chat_output = None
    for node in base["data"]["nodes"]:
        if node["data"]["type"] == "ChatInput" and chat_input is None:
            chat_input = json.loads(json.dumps(node))
            chat_input["data"]["id"] = "ChatInput-A2A"
            chat_input["id"] = "ChatInput-A2A"
            chat_input["data"]["node"]["template"]["input_value"]["value"] = (
                "Je veux un parcours, des ressources et un quiz pour devenir Data Analyst."
            )
        if node["data"]["type"] == "ChatOutput" and chat_output is None:
            chat_output = json.loads(json.dumps(node))
            chat_output["data"]["id"] = "ChatOutput-A2A"
            chat_output["id"] = "ChatOutput-A2A"

    template = {
        "_type": "Component",
        "question": _input_field("question", "MessageInput", "Question / tâche", "", ["Message"]),
        "learner_id": _input_field("learner_id", "StrInput", "Apprenant", "L001"),
        "objective": _input_field("objective", "StrInput", "Objectif", "Devenir Data Analyst"),
        "target_skill": _input_field("target_skill", "StrInput", "Compétence cible", "data-analysis"),
        "orchestrator_url": _input_field(
            "orchestrator_url", "StrInput", "URL de l'orchestrateur", "http://127.0.0.1:8001/orchestrate"
        ),
        "code": _code_field(A2A_CODE),
    }
    orchestrator = {
        "data": {
            "id": "A2AOrchestrator-01",
            "node": {
                "base_classes": ["Message"],
                "beta": False,
                "conditional_paths": [],
                "custom_fields": {},
                "description": (
                    "Découverte des AgentCards, délégation parallèle aux agents Tuteur, Évaluation et "
                    "Orientation, agrégation de la réponse et du correlation_id."
                ),
                "display_name": "Orchestrateur A2A · découverte + délégation",
                "documentation": "",
                "edited": True,
                "field_order": ["question", "learner_id", "objective", "target_skill", "orchestrator_url"],
                "frozen": False,
                "icon": "network",
                "legacy": False,
                "lf_version": "1.7.0",
                "metadata": {
                    "code_hash": uuid.uuid5(uuid.NAMESPACE_URL, "edumcp-a2a-orchestrator").hex[:12],
                    "dependencies": {
                        "dependencies": [
                            {"name": "lfx", "version": "0.2.1"},
                            {"name": "requests", "version": None},
                        ],
                        "total_dependencies": 2,
                    },
                    "module": "custom_components.orchestrateur_a2a_eduagentic",
                },
                "minimized": False,
                "output_types": [],
                "outputs": [
                    {
                        "allows_loop": False,
                        "cache": True,
                        "display_name": "Réponse A2A",
                        "group_outputs": False,
                        "method": "run_orchestration",
                        "name": "response",
                        "selected": "Message",
                        "tool_mode": False,
                        "types": ["Message"],
                        "value": "__UNDEFINED__",
                    }
                ],
                "pinned": False,
                "template": template,
            },
            "type": "CustomComponent",
        },
        "id": "A2AOrchestrator-01",
        "position": {"x": 420, "y": 220},
        "type": "CustomComponent",
    }

    def note(node_id: str, description: str, x: int, y: int):
        return {
            "data": {
                "id": node_id,
                "node": {"description": description, "display_name": "", "documentation": "", "template": {}},
                "type": "note",
            },
            "id": node_id,
            "position": {"x": x, "y": y},
            "type": "note",
        }

    cards_note = note(
        "note-A2A-Cards",
        "# AgentCards · J34\n\n"
        "Chaque agent publie sa carte sur `/.well-known/agent.json` :\n\n"
        "- **Agent Tuteur** · port 8101 · `search_courses`, `recommend_learning_path`\n"
        "- **Agent Évaluation** · port 8102 · `generate_quiz`, `grade_quiz`\n"
        "- **Agent Orientation** · port 8103 · `skill_gap`, `career_path`\n\n"
        "L'orchestrateur lit les cartes, sélectionne les spécialistes et délègue via JSON-RPC 2.0.",
        -60,
        -250,
    )
    protocol_note = note(
        "note-A2A-Protocol",
        "# Protocole A2A 0.3\n\n"
        "1. **Discovery** : `GET /.well-known/agent.json`\n"
        "2. **Delegation** : `POST /` avec `message/send`\n"
        "3. **Task** : `id`, `status`, `artifacts`\n"
        "4. **Trace** : `correlation_id` + logs horodatés\n\n"
        "Le workflow appelle `http://127.0.0.1:8001/orchestrate` ; l'orchestrateur peut aussi être "
        "appelé en JSON-RPC sur `http://127.0.0.1:8001/`.",
        930,
        -250,
    )

    nodes = [chat_input, orchestrator, chat_output, cards_note, protocol_note]
    # edges
    def edge(source, source_name, source_type, target, target_field, target_types, target_type="str"):
        source_handle = {
            "dataType": source_type,
            "id": source,
            "name": source_name,
            "output_types": [source_type if source_type != "ChatInput" else "Message"],
        }
        target_handle = {"fieldName": target_field, "id": target, "inputTypes": target_types, "type": target_type}
        return {
            "animated": False,
            "className": "",
            "data": {"sourceHandle": source_handle, "targetHandle": target_handle},
            "id": f"xy-edge__{source}-{target}-{target_field}",
            "selected": False,
            "source": source,
            "sourceHandle": json.dumps(source_handle, ensure_ascii=False),
            "target": target,
            "targetHandle": json.dumps(target_handle, ensure_ascii=False),
        }

    edges = [
        edge("ChatInput-A2A", "message", "ChatInput", "A2AOrchestrator-01", "question", ["Message"], "str"),
        edge(
            "A2AOrchestrator-01",
            "response",
            "CustomComponent",
            "ChatOutput-A2A",
            "input_value",
            ["Data", "DataFrame", "Message"],
            "other",
        ),
    ]
    payload = {
        "data": {"edges": edges, "nodes": nodes, "viewport": {"x": 0, "y": 0, "zoom": 0.55}},
        "description": (
            "Orchestrateur A2A EduAgentic : découverte des AgentCards, délégation JSON-RPC "
            "aux agents Tuteur, Évaluation et Orientation, agrégation et correlation_id."
        ),
        "endpoint_name": None,
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "edumcp-a2a-flow")),
        "is_component": False,
        "last_tested_version": "1.7.0",
        "name": "Agentic_AI_EdTech_J34_A2A_Final",
        "tags": ["edtech", "a2a", "langflow", "j34", "agentcard", "orchestrateur"],
    }
    path = JSON_DIR / "Agentic_AI_EdTech_J34_A2A_Final.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_registry() -> Path:
    cards = a2a_core.save_agent_cards()
    for src in cards:
        shutil.copy2(src, JSON_DIR / "agent_cards" / src.name)
    registry = {
        "protocol": "A2A 0.3.0",
        "transport": "JSON-RPC 2.0 over HTTP",
        "generated": "2026-11-11",
        "orchestrator": a2a_core.agent_card("orchestrateur"),
        "agents": [
            {
                "agent_id": agent_id,
                "label": a2a_core.AGENT_LABELS[agent_id],
                "port": a2a_core.AGENT_PORTS[agent_id],
                "card_url": f"http://127.0.0.1:{a2a_core.AGENT_PORTS[agent_id]}/.well-known/agent.json",
                "rpc_url": f"http://127.0.0.1:{a2a_core.AGENT_PORTS[agent_id]}/",
                "card": a2a_core.agent_card(agent_id),
            }
            for agent_id in ("agent-tuteur", "agent-evaluation", "agent-orientation")
        ],
        "ports": a2a_core.AGENT_PORTS,
    }
    path = JSON_DIR / "a2a_registry.json"
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    paths = [build_mcp(), build_a2a(), build_registry()]
    for path in paths:
        print(f"  {path.name}: {path.stat().st_size/1024:.0f} Ko")


if __name__ == "__main__":
    main()
