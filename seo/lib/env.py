import os
from pathlib import Path


def load_env_file(*paths: str) -> None:
    """Load env files in order; later files override earlier ones. System env wins over all."""
    merged: dict[str, str] = {}
    for path in paths:
        env_path = Path(path)
        if not env_path.exists():
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    merged[key] = value
    for key, value in merged.items():
        if key not in os.environ:
            os.environ[key] = value
