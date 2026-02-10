import json
import re
from typing import Dict, Any, List

def _parse_requirements_txt(text: str) -> List[str]:
    pkgs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=!~]", line, maxsplit=1)[0].strip()
        if name:
            pkgs.append(name)
    return sorted(set(pkgs))

def _parse_package_lock(text: str) -> List[str]:
    data = json.loads(text)
    deps = data.get("dependencies", {}) or {}
    return sorted(set(deps.keys()))

def _parse_pyproject(text: str) -> List[str]:
    pkgs = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("["):
            continue
        s = s.strip('"').strip("'")
        if any(op in s for op in ["<", ">", "=", "~"]):
            name = re.split(r"[<>=!~]", s, maxsplit=1)[0].strip()
            if name and " " not in name and len(name) <= 80:
                name = name.split("[", 1)[0].strip()
                if name:
                    pkgs.add(name)
    return sorted(pkgs)

def detect_and_extract_packages(filename: str, raw: bytes) -> Dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    fn = filename.lower()

    if fn.endswith("requirements.txt"):
        pkgs = _parse_requirements_txt(text)
        eco = "PyPI"
        kind = "requirements.txt"
    elif fn.endswith("package-lock.json"):
        pkgs = _parse_package_lock(text)
        eco = "npm"
        kind = "package-lock.json"
    elif fn.endswith("pyproject.toml"):
        pkgs = _parse_pyproject(text)
        eco = "PyPI"
        kind = "pyproject.toml"
    else:
        return {
            "ok": False,
            "error": "Unsupported file type.",
            "supported": ["requirements.txt", "pyproject.toml", "package-lock.json"],
            "hint": "Upload requirements.txt, pyproject.toml, or package-lock.json",
        }

    if not pkgs:
        return {"ok": False, "error": f"No packages detected in {kind}."}

    return {"ok": True, "type": kind, "ecosystem": eco, "packages": pkgs}
