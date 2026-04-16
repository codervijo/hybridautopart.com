import pytest
from pathlib import Path
from lib.prompts import load_prompt, load_system_prompt, prompt_hash, validate_template_vars


# ---------------------------------------------------------------------------
# load_prompt
# ---------------------------------------------------------------------------

def test_load_prompt_reads_file(tmp_path):
    (tmp_path / "user.txt").write_text("  hello  ", encoding="utf-8")
    assert load_prompt("user", tmp_path) == "hello"


def test_load_prompt_strips_whitespace(tmp_path):
    (tmp_path / "system.txt").write_text("\n\ncontent\n\n", encoding="utf-8")
    assert load_prompt("system", tmp_path) == "content"


def test_load_prompt_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent", tmp_path)


# ---------------------------------------------------------------------------
# load_system_prompt
# ---------------------------------------------------------------------------

def test_load_system_prompt_combines_persona_and_stage(tmp_path):
    lib_dir = Path(__file__).resolve().parent.parent / "lib"
    persona = (lib_dir / "persona.txt").read_text(encoding="utf-8").strip()

    (tmp_path / "system.txt").write_text("Stage rules here.", encoding="utf-8")
    result = load_system_prompt(tmp_path)

    assert result.startswith(persona)
    assert "Stage rules here." in result
    assert result == f"{persona}\n\nStage rules here."


# ---------------------------------------------------------------------------
# prompt_hash
# ---------------------------------------------------------------------------

def test_prompt_hash_is_12_chars(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"hello")
    assert len(prompt_hash(f)) == 12


def test_prompt_hash_consistent(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"hello")
    assert prompt_hash(f) == prompt_hash(f)


def test_prompt_hash_changes_on_content(tmp_path):
    f = tmp_path / "a.txt"
    f.write_bytes(b"hello")
    h1 = prompt_hash(f)
    f.write_bytes(b"world")
    h2 = prompt_hash(f)
    assert h1 != h2


def test_prompt_hash_order_independent(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"aaa")
    b.write_bytes(b"bbb")
    assert prompt_hash(a, b) == prompt_hash(b, a)


def test_prompt_hash_multiple_files(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"aaa")
    b.write_bytes(b"bbb")
    h_both = prompt_hash(a, b)
    h_a = prompt_hash(a)
    assert h_both != h_a


# ---------------------------------------------------------------------------
# validate_template_vars
# ---------------------------------------------------------------------------

def test_validate_passes_when_all_provided():
    validate_template_vars("Hello $name!", {"name": "world"})


def test_validate_passes_with_braced_syntax():
    validate_template_vars("Hello ${name}!", {"name": "world"})


def test_validate_raises_on_missing_named():
    with pytest.raises(ValueError, match="name"):
        validate_template_vars("Hello $name!", {})


def test_validate_raises_on_missing_braced():
    with pytest.raises(ValueError, match="name"):
        validate_template_vars("Hello ${name}!", {})


def test_validate_does_not_raise_for_dollar_dollar_escape():
    # $$ is an escape for a literal $ — not a variable
    validate_template_vars("Price: $$100", {})


def test_validate_lists_all_missing_vars():
    with pytest.raises(ValueError) as exc_info:
        validate_template_vars("$a and $b", {})
    msg = str(exc_info.value)
    assert "a" in msg
    assert "b" in msg


def test_validate_extra_vars_are_ok():
    # Extra provided vars must not raise
    validate_template_vars("Hello $name!", {"name": "world", "extra": "ignored"})


def test_validate_label_appears_in_error(tmp_path):
    with pytest.raises(ValueError, match="my_template.txt"):
        validate_template_vars("$missing", {}, label="my_template.txt")
