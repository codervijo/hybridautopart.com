import hashlib
from pathlib import Path


def load_prompt(name: str, prompts_dir: Path) -> str:
    """Read and return a prompt file by name (without .txt extension)."""
    return (prompts_dir / f"{name}.txt").read_text(encoding="utf-8").strip()


def prompt_hash(*paths: Path) -> str:
    """Return a 12-char SHA-256 hex digest over the given prompt files."""
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        h.update(path.read_bytes())
    return h.hexdigest()[:12]
