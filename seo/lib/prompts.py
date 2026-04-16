import hashlib
from pathlib import Path
from string import Template

LIB_DIR = Path(__file__).parent


def load_prompt(name: str, prompts_dir: Path) -> str:
    """Read and return a prompt file by name (without .txt extension)."""
    return (prompts_dir / f"{name}.txt").read_text(encoding="utf-8").strip()


def load_system_prompt(stage_prompts_dir: Path) -> str:
    """Return shared persona prepended to the stage-specific system prompt."""
    persona = (LIB_DIR / "persona.txt").read_text(encoding="utf-8").strip()
    stage = (stage_prompts_dir / "system.txt").read_text(encoding="utf-8").strip()
    return f"{persona}\n\n{stage}"


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
