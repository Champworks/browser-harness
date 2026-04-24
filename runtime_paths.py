import getpass
import os
import re
import tempfile
from pathlib import Path
from typing import Optional


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_name(name: Optional[str], default: str = "default") -> str:
    raw = (name or "").strip()
    if not raw:
        return default
    cleaned = _SAFE_NAME_RE.sub("-", raw).strip("._-")
    return cleaned[:64] or default


def runtime_name() -> str:
    return sanitize_name(os.environ.get("BU_NAME", "default"))


def runtime_dir() -> Path:
    base = os.environ.get("BU_RUNTIME_DIR")
    if base:
        root = Path(base).expanduser()
    elif os.name != "nt" and hasattr(os, "getuid"):
        root = Path(tempfile.gettempdir()) / f"browser-harness-{os.getuid()}"
    else:
        root = Path(tempfile.gettempdir()) / f"browser-harness-{sanitize_name(getpass.getuser(), 'user')}"
    root.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(root, 0o700)
    return root


def runtime_path(kind: str, name: Optional[str] = None) -> Path:
    safe_name = sanitize_name(name or os.environ.get("BU_NAME", "default"))
    suffixes = {
        "sock": ".sock",
        "pid": ".pid",
        "log": ".log",
        "version_cache": "-version-cache.json",
    }
    if kind not in suffixes:
        raise ValueError(f"unknown runtime path kind: {kind}")
    if kind == "version_cache":
        return runtime_dir() / f"browser-harness{suffixes[kind]}"
    return runtime_dir() / f"bu-{safe_name}{suffixes[kind]}"
