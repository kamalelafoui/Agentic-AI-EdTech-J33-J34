# -*- coding: utf-8 -*-
"""Génère le jeu de données synthétique EdTech (catalogue, apprenants, quiz, traces).

Toutes les données sont fictives. Aucune donnée personnelle réelle n'est utilisée.
Exécution : python scripts/build_data.py
"""
from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

random.seed(33)

COURSES = [
    {
        "id": "PY101",
        "title": "Python pour l'analyse de données",
        "description": "Fondamentaux de Python, pandas et notebooks pour manipuler des données pédagogiques.",
        "provider": "EduLabs",
        "level": "Débutant",
        "duration_h": 20,
        "skills": ["python", "data-analysis"],
        "prerequisites": [],
        "rating": 4.7,
        "enrolled": 1840,
        "completion_rate": 78,
        "modules": 8,
        "language": "Français",
        "certificate": True,
        "tags": ["python", "pandas", "notebook", "débutant"],
    },
    {
        "id": "SQL201",
        "title": "SQL et bases de données éducatives",
        "description": "Interroger, nettoyer et agréger les données d'apprentissage avec SQL.",
        "provider": "DataSchool",
        "level": "Débutant",
        "duration_h": 18,
        "skills": ["sql", "data-analysis"],
        "prerequisites": [],
        "rating": 4.6,
        "enrolled": 1620,
        "completion_rate": 74,
        "modules": 7,
        "language": "Français",
        "certificate": True,
        "tags": ["sql", "requêtes", "base de données", "débutant"],
    },
    {
        "id": "STAT210",
        "title": "Statistiques appliquées à l'éducation",
        "description": "Décrire, tester et interpréter les résultats d'apprentissage avec confiance.",
        "provider": "EduLabs",
        "level": "Intermédiaire",
        "duration_h": 24,
        "skills": ["statistics", "data-analysis"],
        "prerequisites": ["PY101"],
        "rating": 4.8,
        "enrolled": 980,
        "completion_rate": 69,
        "modules": 9,
        "language": "Français",
        "certificate": True,
        "tags": ["statistiques", "A/B test", "inférence", "moyen"],
    },
    {
        "id": "VIZ220",
        "title": "Visualisation de données avec Power BI",
        "description": "Construire des tableaux de bord clairs pour les équipes pédagogiques.",
        "provider": "DataSchool",
        "level": "Intermédiaire",
        "duration_h": 16,
        "skills": ["visualization", "data-analysis"],
        "prerequisites": ["SQL201"],
        "rating": 4.7,
        "enrolled": 1210,
        "completion_rate": 81,
        "modules": 6,
        "language": "Français",
        "certificate": True,
        "tags": ["power bi", "dashboard", "dataviz", "moyen"],
    },
    {
        "id": "ML301",
        "title": "Machine Learning : fondamentaux",
        "description": "Régression, classification et évaluation de modèles avec scikit-learn.",
        "provider": "AI Academy",
        "level": "Avancé",
        "duration_h": 32,
        "skills": ["machine-learning", "python"],
        "prerequisites": ["PY101", "STAT210"],
        "rating": 4.8,
        "enrolled": 760,
        "completion_rate": 62,
        "modules": 11,
        "language": "Français",
        "certificate": True,
        "tags": ["machine learning", "scikit-learn", "modèles", "avancé"],
    },
    {
        "id": "NLP310",
        "title": "NLP et IA générative",
        "description": "Traitement du langage, embeddings et agents conversationnels responsables.",
        "provider": "AI Academy",
        "level": "Avancé",
        "duration_h": 28,
        "skills": ["nlp", "machine-learning"],
        "prerequisites": ["ML301"],
        "rating": 4.9,
        "enrolled": 640,
        "completion_rate": 58,
        "modules": 10,
        "language": "Français",
        "certificate": True,
        "tags": ["nlp", "llm", "rag", "agents", "avancé"],
    },
    {
        "id": "DL320",
        "title": "Deep Learning et réseaux de neurones",
        "description": "Perceptrons, CNN, transformers et entraînement sur GPU.",
        "provider": "AI Academy",
        "level": "Avancé",
        "duration_h": 36,
        "skills": ["deep-learning", "machine-learning"],
        "prerequisites": ["ML301"],
        "rating": 4.7,
        "enrolled": 420,
        "completion_rate": 54,
        "modules": 12,
        "language": "Français",
        "certificate": True,
        "tags": ["deep learning", "pytorch", "transformers", "avancé"],
    },
    {
        "id": "MLO330",
        "title": "MLOps et déploiement de modèles",
        "description": "Industrialiser, surveiller et versionner des modèles en production.",
        "provider": "CloudCampus",
        "level": "Avancé",
        "duration_h": 24,
        "skills": ["mlops", "cloud"],
        "prerequisites": ["ML301"],
        "rating": 4.6,
        "enrolled": 380,
        "completion_rate": 60,
        "modules": 8,
        "language": "Français",
        "certificate": True,
        "tags": ["mlops", "docker", "ci/cd", "cloud", "avancé"],
    },
    {
        "id": "ETH240",
        "title": "Éthique et gouvernance de l'IA",
        "description": "Biais, transparence, RGPD et cadre de confiance pour l'IA éducative.",
        "provider": "Open Ethics",
        "level": "Intermédiaire",
        "duration_h": 12,
        "skills": ["ethics", "governance"],
        "prerequisites": [],
        "rating": 4.9,
        "enrolled": 1450,
        "completion_rate": 86,
        "modules": 5,
        "language": "Français",
        "certificate": True,
        "tags": ["éthique", "biais", "rgpd", "gouvernance", "moyen"],
    },
    {
        "id": "UX110",
        "title": "UX/UI pour produits éducatifs",
        "description": "Concevoir des parcours d'apprentissage accessibles et engageants.",
        "provider": "DesignLab",
        "level": "Débutant",
        "duration_h": 14,
        "skills": ["ux", "design"],
        "prerequisites": [],
        "rating": 4.5,
        "enrolled": 890,
        "completion_rate": 77,
        "modules": 6,
        "language": "Français",
        "certificate": True,
        "tags": ["ux", "ui", "accessibilité", "débutant"],
    },
    {
        "id": "PEDA120",
        "title": "Ingénierie pédagogique augmentée par l'IA",
        "description": "Concevoir des séquences, évaluations et feedbacks assistés par l'IA.",
        "provider": "TeachForward",
        "level": "Intermédiaire",
        "duration_h": 18,
        "skills": ["pedagogy", "instructional-design"],
        "prerequisites": [],
        "rating": 4.8,
        "enrolled": 1120,
        "completion_rate": 83,
        "modules": 7,
        "language": "Français",
        "certificate": True,
        "tags": ["pédagogie", "assessment", "feedback", "enseignants"],
    },
    {
        "id": "DATA350",
        "title": "Projet capstone Data Analyst",
        "description": "Un projet de bout en bout : question, données, analyse, visualisation et restitution.",
        "provider": "DataSchool",
        "level": "Avancé",
        "duration_h": 40,
        "skills": ["data-analysis", "portfolio", "visualization"],
        "prerequisites": ["STAT210", "VIZ220"],
        "rating": 4.9,
        "enrolled": 310,
        "completion_rate": 72,
        "modules": 5,
        "language": "Français",
        "certificate": True,
        "tags": ["capstone", "portfolio", "projet", "data analyst"],
    },
    {
        "id": "GEN130",
        "title": "Prompt engineering et usage responsable des LLM",
        "description": "Écrire des prompts fiables, vérifier les sources et cadrer les usages.",
        "provider": "AI Academy",
        "level": "Débutant",
        "duration_h": 10,
        "skills": ["prompting", "ethics"],
        "prerequisites": [],
        "rating": 4.6,
        "enrolled": 2100,
        "completion_rate": 88,
        "modules": 4,
        "language": "Français",
        "certificate": True,
        "tags": ["prompt", "llm", "fiabilité", "débutant"],
    },
    {
        "id": "CLOUD230",
        "title": "Cloud et data engineering pour l'éducation",
        "description": "Pipelines, stockage et orchestration de données multi-établissements.",
        "provider": "CloudCampus",
        "level": "Intermédiaire",
        "duration_h": 26,
        "skills": ["cloud", "data-engineering"],
        "prerequisites": ["SQL201"],
        "rating": 4.5,
        "enrolled": 520,
        "completion_rate": 65,
        "modules": 9,
        "language": "Français",
        "certificate": True,
        "tags": ["cloud", "etl", "pipeline", "moyen"],
    },
]

LEARNERS = [
    ("L001", "Lina Benali", "Bac+2", "Cohorte Data 2026", "Devenir Data Analyst", "data-analysis", ["PY101", "SQL201"], 82, 68, "Élevé"),
    ("L002", "Omar El Idrissi", "Bac+3", "Cohorte Data 2026", "Data Scientist", "machine-learning", ["PY101", "SQL201", "STAT210"], 76, 54, "Moyen"),
    ("L003", "Sara Amrani", "Bac+5", "Cohorte IA 2026", "Ingénieure IA", "deep-learning", ["PY101", "STAT210", "ML301"], 88, 72, "Élevé"),
    ("L004", "Youssef Berrada", "Bac+3", "Cohorte Data 2026", "Analyste BI", "visualization", ["SQL201", "VIZ220"], 71, 61, "Moyen"),
    ("L005", "Imane Chraibi", "Bac+2", "Cohorte Reconversion", "Data Analyst", "data-analysis", ["PY101"], 64, 35, "Faible"),
    ("L006", "Karim Alaoui", "Bac+5", "Cohorte IA 2026", "ML Engineer", "mlops", ["PY101", "STAT210", "ML301"], 84, 70, "Élevé"),
    ("L007", "Nadia Fassi", "Formation continue", "Cohorte Enseignants", "Enseignante augmentée par l'IA", "pedagogy", ["PEDA120", "GEN130"], 79, 66, "Élevé"),
    ("L008", "Hamza Tazi", "Bac+3", "Cohorte Data 2026", "Data Engineer", "data-engineering", ["SQL201", "CLOUD230"], 73, 58, "Moyen"),
    ("L009", "Salima Mansouri", "Bac+5", "Cohorte IA 2026", "Responsable éthique IA", "ethics", ["ETH240", "GEN130"], 90, 80, "Élevé"),
    ("L010", "Rachid Boulahcen", "Bac+2", "Cohorte Reconversion", "Technicien data", "sql", ["SQL201"], 58, 22, "Faible"),
    ("L011", "Aya El Fassi", "Bac+3", "Cohorte Data 2026", "Data Analyst", "data-analysis", ["PY101", "SQL201", "STAT210"], 81, 64, "Moyen"),
    ("L012", "Mehdi Ouazzani", "Bac+5", "Cohorte IA 2026", "NLP Engineer", "nlp", ["PY101", "STAT210", "ML301", "NLP310"], 86, 74, "Élevé"),
    ("L013", "Sofia Lahlou", "Bac+3", "Cohorte Enseignants", "Conceptrice pédagogique", "instructional-design", ["PEDA120", "UX110"], 77, 63, "Moyen"),
    ("L014", "Adam Benjelloun", "Bac+2", "Cohorte Reconversion", "Data Analyst junior", "data-analysis", ["PY101", "SQL201"], 69, 44, "Moyen"),
    ("L015", "Rim Cherkaoui", "Bac+5", "Cohorte IA 2026", "AI Product Manager", "machine-learning", ["PY101", "STAT210", "ETH240"], 83, 67, "Élevé"),
    ("L016", "Anas Sefrioui", "Bac+3", "Cohorte Data 2026", "Analyste produit", "visualization", ["SQL201"], 66, 39, "Faible"),
    ("L017", "Hajar El Amrani", "Bac+5", "Cohorte Enseignants", "Directrice pédagogique", "pedagogy", ["PEDA120", "ETH240"], 88, 76, "Élevé"),
    ("L018", "Bilal Ziani", "Bac+2", "Cohorte Reconversion", "Support data", "sql", ["SQL201"], 61, 31, "Moyen"),
    ("L019", "Meryem Naciri", "Bac+3", "Cohorte Data 2026", "Data Analyst", "data-analysis", ["PY101", "STAT210"], 74, 57, "Moyen"),
    ("L020", "Yassine Kabbaj", "Bac+5", "Cohorte IA 2026", "MLOps Engineer", "mlops", ["PY101", "ML301", "MLO330"], 87, 78, "Élevé"),
    ("L021", "Kenza Bouzid", "Bac+3", "Cohorte Enseignants", "Formatrice numérique", "pedagogy", ["PEDA120", "GEN130"], 80, 69, "Élevé"),
    ("L022", "Sami Regragui", "Bac+2", "Cohorte Reconversion", "Assistant BI", "visualization", ["SQL201", "VIZ220"], 68, 48, "Moyen"),
    ("L023", "Laila Haddad", "Bac+5", "Cohorte IA 2026", "Chercheuse en IA éducative", "nlp", ["PY101", "STAT210", "ML301"], 91, 82, "Élevé"),
    ("L024", "Nabil Tahiri", "Bac+3", "Cohorte Data 2026", "Data Analyst", "data-analysis", ["PY101", "SQL201", "VIZ220"], 78, 62, "Moyen"),
]

QUIZ = {
    "PY101": [
        ("PY101-Q1", "Quel objet pandas permet de manipuler un tableau de données en deux dimensions ?", ["Une liste", "Un DataFrame", "Un dictionnaire", "Un tuple"], 1, "Le DataFrame est la structure tabulaire de pandas.", "facile"),
        ("PY101-Q2", "Quelle instruction importe la bibliothèque pandas avec l'alias pd ?", ["import pandas as pd", "import pd from pandas", "from pandas import pd", "using pandas as pd"], 0, "La convention est import pandas as pd.", "facile"),
        ("PY101-Q3", "Que fait df.head() ?", ["Supprime les doublons", "Affiche les premières lignes", "Trie le tableau", "Calcule la moyenne"], 1, "head() affiche par défaut les 5 premières lignes.", "facile"),
        ("PY101-Q4", "Quelle méthode calcule la moyenne d'une colonne numérique ?", ["df.mean()", "df.count()", "df.max()", "df.dtypes"], 0, "mean() calcule la moyenne des colonnes numériques.", "moyen"),
        ("PY101-Q5", "Comment remplacer les valeurs manquantes d'une colonne par 0 ?", ["df.fillna(0)", "df.dropna(0)", "df.replace(0)", "df.isna(0)"], 0, "fillna(0) remplace les NaN par 0.", "moyen"),
    ],
    "SQL201": [
        ("SQL201-Q1", "Quelle clause filtre les lignes avant regroupement ?", ["HAVING", "WHERE", "ORDER BY", "GROUP BY"], 1, "WHERE filtre les lignes ; HAVING filtre les groupes.", "facile"),
        ("SQL201-Q2", "Quelle fonction compte le nombre de lignes d'un groupe ?", ["SUM()", "COUNT()", "AVG()", "MAX()"], 1, "COUNT() compte les lignes.", "facile"),
        ("SQL201-Q3", "Quelle jointure conserve toutes les lignes de la table de gauche ?", ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "SELF JOIN"], 1, "LEFT JOIN conserve la table de gauche.", "moyen"),
        ("SQL201-Q4", "Quelle clause s'utilise avec les agrégats pour filtrer les groupes ?", ["WHERE", "HAVING", "LIMIT", "DISTINCT"], 1, "HAVING filtre après GROUP BY.", "moyen"),
        ("SQL201-Q5", "Que fait DISTINCT dans un SELECT ?", ["Trie les résultats", "Supprime les doublons", "Limite à 10 lignes", "Crée un index"], 1, "DISTINCT renvoie des lignes uniques.", "facile"),
    ],
    "STAT210": [
        ("STAT210-Q1", "Que mesure l'écart-type ?", ["La valeur centrale", "La dispersion autour de la moyenne", "Le nombre d'observations", "La corrélation"], 1, "L'écart-type mesure la dispersion.", "facile"),
        ("STAT210-Q2", "Dans un test d'hypothèse, que signifie p < 0,05 ?", ["L'hypothèse nulle est prouvée", "Le résultat est statistiquement significatif au seuil 5 %", "La variable est normale", "L'échantillon est trop grand"], 1, "p < 0,05 conduit à rejeter H0 au seuil 5 %.", "moyen"),
        ("STAT210-Q3", "Quelle mesure est sensible aux valeurs extrêmes ?", ["La médiane", "La moyenne", "Le mode", "L'écart interquartile"], 1, "La moyenne est tirée par les valeurs extrêmes.", "moyen"),
        ("STAT210-Q4", "Un intervalle de confiance à 95 % signifie que…", ["95 % des données sont dans l'intervalle", "La méthode capture le vrai paramètre dans 95 % des échantillonnages", "Le résultat est vrai à 95 %", "Il n'y a pas d'incertitude"], 1, "C'est une propriété de la procédure sur le long terme.", "difficile"),
        ("STAT210-Q5", "Quel test compare les moyennes de deux groupes indépendants ?", ["Test du chi²", "Test t de Student", "ANOVA à un facteur", "Régression logistique"], 1, "Le test t compare deux moyennes indépendantes.", "moyen"),
    ],
    "VIZ220": [
        ("VIZ220-Q1", "Quel graphique montre l'évolution d'une valeur dans le temps ?", ["Diagramme en secteurs", "Courbe", "Nuage de points", "Treemap"], 1, "La courbe est adaptée aux séries temporelles.", "facile"),
        ("VIZ220-Q2", "Quel encodage visuel est le plus précis pour comparer des catégories ?", ["La couleur", "La longueur d'une barre", "La surface", "L'angle"], 1, "La longueur est plus précise que la surface ou l'angle.", "moyen"),
        ("VIZ220-Q3", "Que faut-il éviter dans un tableau de bord ?", ["Un titre clair", "Trop de couleurs et d'indicateurs", "Une source de données", "Un filtre de période"], 1, "La surcharge visuelle nuit à la lecture.", "facile"),
        ("VIZ220-Q4", "Quel graphique est adapté à une distribution de scores ?", ["Histogramme", "Diagramme circulaire", "Carte", "Jauge"], 0, "L'histogramme montre la distribution.", "moyen"),
        ("VIZ220-Q5", "Pourquoi ajouter une ligne de référence sur un graphique ?", ["Décorer", "Situer les valeurs par rapport à un seuil", "Masquer les données", "Remplacer la légende"], 1, "La référence donne du sens aux valeurs.", "moyen"),
    ],
    "ML301": [
        ("ML301-Q1", "Quel est le risque d'un modèle qui apprend par cœur les données d'entraînement ?", ["Le sous-apprentissage", "Le sur-apprentissage", "La multicolinéarité", "Le biais de sélection"], 1, "C'est le sur-apprentissage (overfitting).", "facile"),
        ("ML301-Q2", "À quoi sert un jeu de validation ?", ["À entraîner le modèle", "À choisir les hyperparamètres", "À déployer le modèle", "À collecter les données"], 1, "La validation sert à régler les hyperparamètres.", "moyen"),
        ("ML301-Q3", "Quelle métrique est adaptée à un problème très déséquilibré ?", ["Accuracy", "F1-score", "MSE", "R²"], 1, "Le F1-score équilibre précision et rappel.", "moyen"),
        ("ML301-Q4", "Que fait une validation croisée k-fold ?", ["Elle découpe les données en k plis pour évaluer la robustesse", "Elle supprime k lignes", "Elle crée k modèles en production", "Elle normalise les données"], 0, "Chaque pli sert une fois de validation.", "difficile"),
        ("ML301-Q5", "Quelle tâche prédit une catégorie ?", ["La régression", "La classification", "Le clustering", "La réduction de dimension"], 1, "La classification prédit une classe.", "facile"),
    ],
    "GEN130": [
        ("GEN130-Q1", "Quel est le principal risque d'un LLM utilisé sans vérification ?", ["Une réponse trop courte", "Une hallucination présentée comme un fait", "Un temps de réponse long", "Une interface peu ergonomique"], 1, "Le LLM peut inventer des faits de façon convaincante.", "facile"),
        ("GEN130-Q2", "Que faut-il fournir dans un prompt pour améliorer la fiabilité ?", ["Le contexte, la tâche et le format attendu", "Uniquement une question vague", "Le nom du modèle", "Une émotion"], 0, "Contexte + tâche + format = prompt cadré.", "facile"),
        ("GEN130-Q3", "Pourquoi citer ses sources dans une réponse générée ?", ["Pour allonger la réponse", "Pour permettre la vérification", "Pour éviter le coût", "Pour changer de modèle"], 1, "La citation rend la réponse vérifiable.", "moyen"),
        ("GEN130-Q4", "Qu'est-ce qu'un prompt système ?", ["Une instruction qui cadre le comportement de l'assistant", "Un fichier de données", "Un modèle de langage", "Une clé API"], 0, "Le prompt système définit le rôle et les règles.", "moyen"),
        ("GEN130-Q5", "Quelle pratique réduit le mieux les biais de confirmation ?", ["Demander plusieurs sources et contre-hypothèses", "Accepter la première réponse", "Utiliser un seul exemple", "Augmenter la température"], 0, "La confrontation de sources limite le biais.", "difficile"),
    ],
}


def build_courses() -> None:
    (DATA / "courses.json").write_text(json.dumps(COURSES, ensure_ascii=False, indent=2), encoding="utf-8")


def build_learners() -> None:
    learners = []
    for lid, name, level, cohort, goal, target_skill, completed, avg, progress, engagement in LEARNERS:
        learners.append(
            {
                "id": lid,
                "name": name,
                "level": level,
                "cohort": cohort,
                "goal": goal,
                "target_skill": target_skill,
                "completed_courses": completed,
                "quiz_average": avg,
                "progress_pct": progress,
                "engagement": engagement,
                "joined": "2026-09-15",
                "status": "Actif" if progress < 90 else "Diplômé",
            }
        )
    (DATA / "learners.json").write_text(json.dumps(learners, ensure_ascii=False, indent=2), encoding="utf-8")


def build_quiz() -> None:
    bank = []
    for course_id, questions in QUIZ.items():
        for qid, question, choices, answer, explanation, difficulty in questions:
            bank.append(
                {
                    "id": qid,
                    "course_id": course_id,
                    "question": question,
                    "choices": choices,
                    "answer_index": answer,
                    "explanation": explanation,
                    "difficulty": difficulty,
                }
            )
    (DATA / "quiz_bank.json").write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")


def build_attempts() -> None:
    rows = []
    start = datetime(2026, 9, 15, 9, 0)
    end = datetime(2026, 11, 10, 19, 0)
    learners = {l[0]: (l[1], l[7]) for l in LEARNERS}
    course_ids = list(QUIZ.keys()) + ["DATA350", "ETH240", "PEDA120"]
    course_skill = {c["id"]: c["skills"][0] for c in COURSES}
    for i in range(168):
        lid = random.choice(list(learners))
        cid = random.choice(course_ids)
        base = learners[lid][1]
        difficulty_penalty = {"PY101": 0, "SQL201": 2, "STAT210": -4, "VIZ220": 1, "ML301": -7, "GEN130": 3}.get(cid, -2)
        score = max(38, min(100, int(random.gauss(base + difficulty_penalty, 9))))
        ts = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        duration = random.randint(12, 45)
        rows.append(
            {
                "attempt_id": f"A{i+1:04d}",
                "learner_id": lid,
                "learner_name": learners[lid][0],
                "course_id": cid,
                "skill": course_skill.get(cid, "data-analysis"),
                "score": score,
                "passed": "Oui" if score >= 70 else "Non",
                "attempt_date": ts.strftime("%Y-%m-%d"),
                "duration_min": duration,
                "difficulty": random.choice(["facile", "moyen", "difficile"]),
            }
        )
    rows.sort(key=lambda r: r["attempt_date"])
    with (DATA / "quiz_attempts.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_delegations() -> None:
    rows = []
    targets = [
        ("agent-tuteur", "search_courses", "Recherche de ressources"),
        ("agent-tuteur", "recommend_path", "Recommandation de parcours"),
        ("agent-evaluation", "generate_quiz", "Génération d'un quiz"),
        ("agent-evaluation", "grade_quiz", "Correction d'un quiz"),
        ("agent-orientation", "skill_gap", "Analyse des compétences"),
        ("agent-orientation", "career_path", "Orientation métier"),
    ]
    start = datetime(2026, 10, 12, 8, 30)
    for i in range(84):
        target, skill, task = random.choice(targets)
        ts = start + timedelta(hours=random.randint(0, 29 * 24), minutes=random.randint(0, 59))
        status = random.choices(["completed", "failed", "timeout"], weights=[91, 4, 5])[0]
        latency = random.randint(180, 780) if status == "completed" else random.randint(900, 2600)
        rows.append(
            {
                "correlation_id": f"A2A-{ts.strftime('%y%m%d')}-{i+1:04d}",
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "orchestrateur",
                "target": target,
                "skill": skill,
                "task": task,
                "status": status,
                "latency_ms": latency,
                "learner_id": f"L{random.randint(1,24):03d}",
            }
        )
    rows.sort(key=lambda r: r["timestamp"])
    with (DATA / "a2a_delegations.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_meta() -> None:
    meta = {
        "title": "Agentic AI in Education Technology (EdTech)",
        "subtitle": "MCP & A2A — deux mini-projets",
        "author": "Kamal El Afoui",
        "program": "Centre des Très Petites Entreprises Solidaires · DBA Technology",
        "days": "Jours 33 & 34",
        "date": "11 novembre 2026",
        "version": "1.0.0 — Correction finale",
        "dashboard_port": 8011,
        "mcp_port": 8000,
        "a2a_orchestrator_port": 8001,
        "mcp_url": "http://127.0.0.1:8000/sse",
        "a2a_url": "http://127.0.0.1:8001",
        "license": "MIT — données synthétiques",
    }
    (DATA / "site.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    build_courses()
    build_learners()
    build_quiz()
    build_attempts()
    build_delegations()
    build_meta()
    print("Données générées dans", DATA)
    print(f"  {len(COURSES)} cours · {len(LEARNERS)} apprenants · {sum(len(v) for v in QUIZ.values())} questions")


if __name__ == "__main__":
    main()
