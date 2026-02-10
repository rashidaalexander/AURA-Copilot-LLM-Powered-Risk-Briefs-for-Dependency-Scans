import requests
from typing import Dict, List, Any

OSV_QUERY_URL = "https://api.osv.dev/v1/query"

def _query_single(name: str, ecosystem: str) -> Dict[str, Any]:
    payload = {"package": {"name": name, "ecosystem": ecosystem}}
    r = requests.post(OSV_QUERY_URL, json=payload, timeout=25)
    r.raise_for_status()
    return r.json()

def query_osv_bulk(packages: List[str], ecosystem: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for pkg in packages:
        try:
            raw = _query_single(pkg, ecosystem)
            vulns = raw.get("vulns", []) or []
            results.append({
                "package": pkg,
                "ecosystem": ecosystem,
                "vuln_count": len(vulns),
                "vulnerabilities": [
                    {
                        "id": v.get("id"),
                        "summary": v.get("summary"),
                        "details": (v.get("details") or "")[:800],
                        "aliases": v.get("aliases", []),
                        "severity": v.get("severity", []),
                        "references": v.get("references", []),
                    }
                    for v in vulns
                ],
            })
        except Exception as e:
            results.append({
                "package": pkg,
                "ecosystem": ecosystem,
                "vuln_count": 0,
                "error": str(e),
                "vulnerabilities": [],
            })
    return results
