# Publication GitHub

Dépôt publié : **https://github.com/kamalelafoui/Agentic-AI-EdTech-J33-J34**

Le dépôt local est prêt. L'URI MongoDB est dans `.env` et **ne doit jamais être poussée**.

## 1. Vérifier que `.env` est ignoré

```powershell
git status --short
# .env ne doit pas apparaître
git check-ignore -v .env
```

## 2. Créer le dépôt et pousser

```powershell
git init
git add .
git commit -m "EduAgentic J33/J34 — MCP & A2A, correction finale"
git branch -M main
git remote add origin https://github.com/kamalelafoui/Agentic-AI-EdTech-J33-J34.git
git push -u origin main
```

Si le dépôt doit être privé, le créer d'abord sur GitHub en **Private**, puis pousser.

## 3. Fichiers exclus

- `.env` (secret)
- `a2a/logs/`
- `screenshots/_*`
- `videos/_*`
- `data/a2a_live.jsonl`
- archives `*.zip`
- environnements virtuels et `__pycache__`

Les vidéos peuvent être ajoutées avec Git LFS si elles dépassent la limite de GitHub :

```powershell
git lfs install
git lfs track "videos/*.mp4"
git add .gitattributes videos/
git commit -m "Ajout des vidéos de démonstration"
git push
```

## 4. Description suggérée du dépôt

> EduAgentic — deux mini-projets Agentic AI in Education Technology : serveur MCP FastMCP (6 outils EdTech), système multi-agents A2A (AgentCards, découverte, délégation, correlation_id), dashboard Streamlit 8011, documentation, présentations et vidéos.

## 5. Tags

`agentic-ai`, `edtech`, `mcp`, `a2a`, `langflow`, `streamlit`, `python`, `education`, `multi-agent`.
