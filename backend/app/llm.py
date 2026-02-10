import os
import json
import requests
from typing import List, Dict, Any

def _safe_trim_results(osv_results: List[Dict[str, Any]], max_vulns: int = 25) -> List[Dict[str, Any]]:
    # keep output compact so local LLMs don't choke
    trimmed = []
    kept = 0
    for r in osv_results:
        vulns = r.get("vulnerabilities", []) or []
        if not vulns:
            continue
        take = vulns[: max(0, max_vulns - kept)]
        kept += len(take)
        trimmed.append({
            "package": r.get("package"),
            "ecosystem": r.get("ecosystem"),
            "vuln_count": r.get("vuln_count", 0),
            "vulnerabilities": [
                {
                    "id": v.get("id"),
                    "summary": v.get("summary"),
                    "aliases": v.get("aliases", []),
                }
                for v in take
            ],
        })
        if kept >= max_vulns:
            break
    return trimmed

def generate_executive_brief(osv_results: List[Dict[str, Any]], risk_score: int) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return _openai_brief(osv_results, risk_score)
    return _ollama_brief(osv_results, risk_score)

def _ollama_brief(osv_results: List[Dict[str, Any]], risk_score: int) -> str:
    # Default: local Ollama (no API key). Requires Docker service or local ollama running.
    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    payload_data = _safe_trim_results(osv_results)
    prompt = f"""You are a defensive security analyst.
Write an executive brief (max 10 bullets) for a software team based on the findings below.

Requirements:
- Start with a one-line summary including the risk score: {risk_score}/100
- Give 3 priority actions (what to do first)
- Call out any packages that appear multiple times or look high-impact
- Keep it practical and non-alarmist

Findings (JSON):
{json.dumps(payload_data, indent=2)}
"""

    try:
        r = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip() or "LLM returned an empty response."
    except Exception as e:
        return (
            "LLM brief unavailable. "
            "If you're using Docker, ensure the 'ollama' service is running and the model is pulled. "
            f"Details: {e}"
        )

def _openai_brief(osv_results: List[Dict[str, Any]], risk_score: int) -> str:
    # Optional: set LLM_PROVIDER=openai and OPENAI_API_KEY
    # Uses the OpenAI Responses API endpoint via HTTPS.
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return "OPENAI_API_KEY is not set. Set it or use LLM_PROVIDER=ollama."

    payload_data = _safe_trim_results(osv_results)
    instructions = (
        "You are a defensive security analyst. "
        "Write an executive brief (max 10 bullets) for a software team. "
        f"Include the risk score {risk_score}/100 in the first line, then 3 priority actions."
    )

    # Minimal implementation using the Responses API style fields
    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                "input": [
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": json.dumps(payload_data)},
                ],
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        # best-effort extraction
        out = ""
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out += c.get("text", "")
        return out.strip() or "OpenAI returned an empty response."
    except Exception as e:
        return f"OpenAI brief failed: {e}"
