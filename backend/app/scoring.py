from typing import List, Dict, Any

def compute_risk_score(results: List[Dict[str, Any]]) -> int:
    score = 0
    for r in results:
        vc = int(r.get("vuln_count", 0) or 0)
        score += vc * 8
        for v in (r.get("vulnerabilities", []) or []):
            if v.get("severity"):
                score += 3
    return min(100, score)
