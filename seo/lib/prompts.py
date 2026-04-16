import hashlib
from pathlib import Path
from string import Template


def load_prompt(name: str, prompts_dir: Path) -> str:
    """Read and return a prompt file by name (without .txt extension)."""
    return (prompts_dir / f"{name}.txt").read_text(encoding="utf-8").strip()


def prompt_hash(*paths: Path) -> str:
    """Return a 12-char SHA-256 hex digest over the given prompt files."""
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


def validate_template_vars(template_str: str, provided: dict, label: str = "") -> None:
    """Raise ValueError if any $-style template variable in template_str is missing from provided."""
    # Use Template's own pattern to extract identifiers (handles $$ escapes correctly)
    required = {
        m.group("named") or m.group("braced")
        for m in Template.pattern.finditer(template_str)
        if m.group("named") or m.group("braced")
    }
    missing = required - set(provided)
    if missing:
        where = f" in {label}" if label else ""
        raise ValueError(f"Missing template variable(s){where}: {', '.join(sorted(missing))}")
