from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
DATASET = ROOT / "dataset"
REPOS = DATASET / "repos"
LOGS = DATASET / "logs"
RAW = DATASET / "raw"
DATABASE = DATASET / "setupbench-lens.sqlite"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def command_output(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, encoding="utf-8", errors="replace").strip()


def gh_executable() -> str:
    candidates = [
        os.environ.get("GH_PATH"),
        "gh",
        r"C:\Program Files\GitHub CLI\gh.exe",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            subprocess.run([candidate, "--version"], capture_output=True, check=True)
            return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("GitHub CLI was not found. Install and authenticate gh first.")


SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)(\s*[=:]\s*)([^\s,'\";]+)"),
    re.compile(r"(?i)(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\b(?:gh[opsu]_|sk-|re_)[A-Za-z0-9_-]{8,}\b"),
]


def redact(text: str) -> str:
    result = text
    result = SECRET_PATTERNS[0].sub(lambda m: f"{m.group(1)}{m.group(2)}<REDACTED>", result)
    for pattern in SECRET_PATTERNS[1:]:
        result = pattern.sub("<REDACTED>", result)
    return result


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

