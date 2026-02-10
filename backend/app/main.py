import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from .parsers import detect_and_extract_packages
from .osv_client import query_osv_bulk
from .scoring import compute_risk_score
from .llm import generate_executive_brief

app = FastAPI(title="AURA Copilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "aura-copilot",
        "llm_provider": os.getenv("LLM_PROVIDER", "ollama"),
    }

@app.post("/scan")
async def scan(file: UploadFile = File(...)):
    raw = await file.read()
    filename = (file.filename or "upload").lower()

    parsed = detect_and_extract_packages(filename, raw)
    if not parsed["ok"]:
        return parsed

    eco = parsed["ecosystem"]
    pkgs = parsed["packages"]
    osv_results = query_osv_bulk(pkgs, ecosystem=eco)

    score = compute_risk_score(osv_results)
    return {
        "ok": True,
        "filename": file.filename,
        "ecosystem": eco,
        "packages_scanned": len(pkgs),
        "risk_score": score,
        "results": osv_results,
    }

@app.post("/scan-and-brief")
async def scan_and_brief(file: UploadFile = File(...)):
    raw = await file.read()
    filename = (file.filename or "upload").lower()

    parsed = detect_and_extract_packages(filename, raw)
    if not parsed["ok"]:
        return parsed

    eco = parsed["ecosystem"]
    pkgs = parsed["packages"]
    osv_results = query_osv_bulk(pkgs, ecosystem=eco)

    score = compute_risk_score(osv_results)
    brief = generate_executive_brief(osv_results=osv_results, risk_score=score)

    return {
        "ok": True,
        "filename": file.filename,
        "ecosystem": eco,
        "packages_scanned": len(pkgs),
        "risk_score": score,
        "executive_brief": brief,
        "results": osv_results,
    }
