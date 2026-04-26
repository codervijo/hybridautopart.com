#!/usr/bin/env python3
"""
WordPress Plugin Builder — autonomous pipeline.

Reads idea files from IDEAS_DIR (default: ideas/), runs a two-stage LLM pipeline
to generate a complete React + WordPress plugin, writes files, and optionally
builds the JS bundle via Docker.

Stages per idea:
  1. spec      — idea.md  → .spec.json  (structured plugin spec)
  2. generate  — spec.json → .files.json (all source file contents)
  3. write     — .files.json → plugin directory tree
  4. build     — docker run → plugin/dist/*.js + *.css
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from string import Template

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.env import load_env_file
from lib.http import error_code_for, with_retry
from lib.io import atomic_write, log, utc_now
from lib.run_state import RunState

BUILDER_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BUILDER_DIR / "prompts"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def get_config() -> dict:
    load_env_file(str(BUILDER_DIR / "builder.env"))
    return {
        "api_key":      os.environ.get("API_KEY", ""),
        "api_url":      os.environ.get("API_URL", "https://api.anthropic.com/v1/messages"),
        "model":        os.environ.get("MODEL", "claude-opus-4-6"),
        "max_tokens":   int(os.environ.get("MAX_TOKENS", "16000")),
        "timeout":      int(os.environ.get("TIMEOUT", "180")),
        "max_retries":  int(os.environ.get("MAX_RETRIES", "3")),
        "delay_ms":     int(os.environ.get("DELAY_MS", "2000")),
        "ideas_dir":    Path(os.environ.get("IDEAS_DIR", str(BUILDER_DIR / "ideas"))),
        "output_dir":   Path(os.environ.get("OUTPUT_DIR", str(BUILDER_DIR / "output"))),
        "docker_build": os.environ.get("DOCKER_BUILD", "true").lower() == "true",
        "docker_image": os.environ.get("DOCKER_IMAGE", "node:20-slim"),
    }


# ---------------------------------------------------------------------------
# LLM — native Anthropic Messages API
# ---------------------------------------------------------------------------

def call_llm(system: str, user: str, config: dict) -> str:
    """Call the Anthropic Messages API and return the assistant text."""
    payload = json.dumps({
        "model":      config["model"],
        "max_tokens": config["max_tokens"],
        "system":     system,
        "messages":   [{"role": "user", "content": user}],
    }).encode()

    req = urllib.request.Request(
        config["api_url"],
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         config["api_key"],
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=config["timeout"]) as resp:
        result = json.loads(resp.read().decode())

    return result["content"][0]["text"]


def extract_json(text: str) -> str:
    """Strip markdown code fences if present, returning raw JSON string."""
    text = text.strip()
    # ```json ... ``` or ``` ... ```
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# Stage 1: idea → spec
# ---------------------------------------------------------------------------

def run_spec_stage(idea_text: str, config: dict) -> dict:
    system = load_prompt("system")
    user_tmpl = load_prompt("spec")
    user = Template(user_tmpl).substitute(idea=idea_text)

    raw = with_retry(
        lambda: call_llm(system, user, config),
        max_retries=config["max_retries"],
        label="spec",
    )
    return json.loads(extract_json(raw))


# ---------------------------------------------------------------------------
# Stage 2: spec → files
# ---------------------------------------------------------------------------

def run_generate_stage(spec: dict, config: dict) -> list[dict]:
    system = load_prompt("system")
    user_tmpl = load_prompt("generate")
    user = Template(user_tmpl).substitute(spec=json.dumps(spec, indent=2))

    raw = with_retry(
        lambda: call_llm(system, user, config),
        max_retries=config["max_retries"],
        label="generate",
    )
    return json.loads(extract_json(raw))


# ---------------------------------------------------------------------------
# Stage 3: write files
# ---------------------------------------------------------------------------

MAKEFILE_TEMPLATE = """\
PIPELINE_NAME := {slug}
ifeq ($$(shell [ -f /.dockerenv ] && echo yes),yes)
  BUILDER_PATH ?= /usr/builder
else
  BUILDER_PATH ?= $$(HOME)/work/projects/builder
endif
STACK      := react
WEBAPP_DIR := webapp
include $$(BUILDER_PATH)/Makefile
"""

MAKEFILE_LOCAL_TEMPLATE = """\
export CONTAINER_NAME := {slug}-build
export DOCKER_CMD     := docker
"""

def write_plugin_files(plugin_dir: Path, files: list[dict], spec: dict) -> None:
    slug = spec["plugin_slug"]

    for entry in files:
        rel_path = entry["path"].lstrip("/")
        dest = plugin_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(dest, entry["content"])
        log(f"    write {rel_path}")

    # Always write Makefile and Makefile.local from templates (infra-specific)
    atomic_write(plugin_dir / "Makefile",       MAKEFILE_TEMPLATE.format(slug=slug))
    atomic_write(plugin_dir / "Makefile.local", MAKEFILE_LOCAL_TEMPLATE.format(slug=slug))
    log("    write Makefile")
    log("    write Makefile.local")


# ---------------------------------------------------------------------------
# Stage 4: Docker build
# ---------------------------------------------------------------------------

DOCKER_BUILD_SH = """\
set -e
echo "[build] Installing pnpm..."
npm install -g pnpm@10 --quiet 2>&1 | tail -1

echo "[build] pnpm install..."
pnpm install

echo "[build] Fixing esbuild binary if needed..."
ESBUILD_INSTALL=$(find node_modules/.pnpm -name 'install.js' | grep '/esbuild-' | head -1 || true)
if [ -n "$ESBUILD_INSTALL" ]; then
  node "$ESBUILD_INSTALL" 2>/dev/null || true
fi

echo "[build] Building..."
pnpm build
echo "[build] Done."
"""

def run_docker_build(plugin_dir: Path, slug: str, config: dict) -> None:
    container = f"pgx-build-{slug}"
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "--name", container,
            "-v", f"{plugin_dir.resolve()}:/usr/src/app",
            "--workdir", "/usr/src/app/webapp",
            config["docker_image"],
            "sh", "-c", DOCKER_BUILD_SH,
        ],
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"docker build exited {result.returncode} for {slug}")


# ---------------------------------------------------------------------------
# Per-idea build
# ---------------------------------------------------------------------------

def _spec_file(plugin_dir: Path) -> Path:
    return plugin_dir / ".spec.json"

def _files_file(plugin_dir: Path) -> Path:
    return plugin_dir / ".files.json"

def _app_jsx(plugin_dir: Path) -> Path:
    return plugin_dir / "webapp" / "src" / "App.jsx"

def _dist_marker(plugin_dir: Path, slug: str) -> Path:
    return plugin_dir / "plugin" / "dist" / f"{slug}.js"


def build_idea(idea_path: Path, config: dict, state: RunState) -> None:
    slug = idea_path.stem       # e.g. "vin-checker"
    output_dir: Path = config["output_dir"]
    plugin_dir = output_dir / slug

    log(f"\n{'='*60}")
    log(f"Idea: {idea_path.name}  →  {plugin_dir}")

    # ── Stage 1: Spec ──────────────────────────────────────────
    if _spec_file(plugin_dir).exists():
        log("[1/4] spec: already done — loading")
        spec = json.loads(_spec_file(plugin_dir).read_text())
    else:
        log("[1/4] spec: calling LLM...")
        idea_text = idea_path.read_text(encoding="utf-8")
        spec = run_spec_stage(idea_text, config)
        plugin_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(_spec_file(plugin_dir), json.dumps(spec, indent=2, ensure_ascii=False))
        log(f"  plugin_slug: {spec.get('plugin_slug')}  shortcode: [{spec.get('shortcode')}]")

    real_slug = spec.get("plugin_slug", slug)

    # ── Stage 2: Generate file contents ────────────────────────
    if _files_file(plugin_dir).exists():
        log("[2/4] generate: already done — loading")
        files = json.loads(_files_file(plugin_dir).read_text())
    else:
        log("[2/4] generate: calling LLM (this may take a minute)...")
        files = run_generate_stage(spec, config)
        atomic_write(_files_file(plugin_dir), json.dumps(files, indent=2, ensure_ascii=False))
        log(f"  {len(files)} file(s) generated")

    # ── Stage 3: Write files ────────────────────────────────────
    if _app_jsx(plugin_dir).exists():
        log("[3/4] write: already done — skipping")
    else:
        log("[3/4] write: writing files...")
        write_plugin_files(plugin_dir, files, spec)
        log(f"  wrote to {plugin_dir}")

    # ── Stage 4: Docker build ───────────────────────────────────
    if _dist_marker(plugin_dir, real_slug).exists():
        log("[4/4] build: already done — skipping")
    elif not config["docker_build"]:
        log("[4/4] build: SKIPPED (DOCKER_BUILD=false)")
        log(f"  cd {plugin_dir} && make build")
    else:
        log("[4/4] build: running docker...")
        run_docker_build(plugin_dir, real_slug, config)
        dist = _dist_marker(plugin_dir, real_slug)
        if dist.exists():
            size_kb = dist.stat().st_size // 1024
            log(f"  OK — dist/{real_slug}.js  {size_kb} kB")
        else:
            log("  WARNING: dist file not found after build — check logs above")

    state.record_success(slug, plugin_dir, plugin_slug=real_slug)
    log(f"\nDone: {slug}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    config = get_config()

    if not config["api_key"]:
        log("ERROR [NO_API_KEY]: API_KEY is not set.")
        log("  Set it in plugin-builder/builder.env:  API_KEY=sk-ant-...")
        log("  or:  export API_KEY=...")
        sys.exit(1)

    ideas_dir: Path  = config["ideas_dir"]
    output_dir: Path = config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    idea_files = sorted(ideas_dir.glob("*.md"))
    if not idea_files:
        log(f"No idea files found in {ideas_dir}")
        log("  Create a .md file describing your plugin and re-run.")
        sys.exit(0)

    log(f"Plugin Builder")
    log(f"  Model:      {config['model']}")
    log(f"  Ideas dir:  {ideas_dir}  ({len(idea_files)} idea(s))")
    log(f"  Output dir: {output_dir}")
    log(f"  Docker:     {'yes' if config['docker_build'] else 'no'}")

    state = RunState(output_dir)

    total = len(idea_files)
    success_count = 0
    failed_count  = 0
    skipped_count = 0

    for i, idea_path in enumerate(idea_files):
        slug = idea_path.stem
        if state.is_done(slug):
            log(f"\n[{i+1}/{total}] SKIP {slug} (already completed)")
            skipped_count += 1
            continue

        log(f"\n[{i+1}/{total}] Building: {slug}")
        try:
            build_idea(idea_path, config, state)
            success_count += 1
        except Exception as e:
            code = error_code_for(e)
            log(f"\nFAILED [{code}]: {slug} — {e}")
            state.record_failure(slug, e, config["max_retries"], code)
            failed_count += 1

        delay_s = config["delay_ms"] / 1000.0
        if delay_s > 0 and i < total - 1:
            log(f"\nsleeping {delay_s:.1f}s...")
            time.sleep(delay_s)

    log(f"\n{'='*60}")
    state.write_summary(total=total, success=success_count,
                        failed=failed_count, skipped=skipped_count)
    log(f"Done. total={total} success={success_count} "
        f"failed={failed_count} skipped={skipped_count}")


if __name__ == "__main__":
    run()
