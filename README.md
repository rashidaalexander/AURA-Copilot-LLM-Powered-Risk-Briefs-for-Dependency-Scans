# AURA Copilot — LLM-Powered Risk Briefs for Dependency Scans

AURA Copilot is a **deployable defensive** app that:
1) scans dependency manifests using the **OSV** advisory database  
2) computes an explainable **risk score (0–100)**  
3) generates an **LLM executive brief** you can paste into tickets or reports

**Stack:** FastAPI + minimal Web UI + Docker Compose + GitHub Actions CI  
**Default LLM:** local **Ollama** (no API keys)

## One-command run (Docker)
```bash
docker compose up --build
```

- Web UI: http://localhost:8080  
- API: http://localhost:8000/health  

## Use it
In the Web UI, upload:
- `requirements.txt`
- `pyproject.toml`
- `package-lock.json`

Then click **Scan + Brief**.

## Notes about “deployable immediately”
- The containers start immediately.
- On first run, **Ollama will download the model once** (one-time). After that, it’s cached in the Docker volume.

## Optional: use OpenAI instead of Ollama
In `docker-compose.yml`, set:
- `LLM_PROVIDER=openai`
- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=...`

## License
MIT
