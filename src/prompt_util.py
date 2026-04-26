"""
prompt_util.py

Load prompt text from prompts/ directory.
Key dependencies: pathlib
"""

from __future__ import annotations

from pathlib import Path


def load_prompt(name: str, base: Path | None = None) -> str:
    """Load prompts/{name} (.txt or .yaml content as text)."""
    root = base or Path(__file__).resolve().parent.parent / "prompts"
    for ext in (".txt", ".yaml", ".md"):
        p = root / f"{name}{ext}"
        if p.is_file():
            return p.read_text(encoding="utf-8")
    p = root / name
    if p.is_file():
        return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"prompt not found: {name} under {root}")


def load_prompt_body(name: str, base: Path | None = None) -> str:
    """Load prompt file and strip leading # comment block (PRD prompt headers)."""
    text = load_prompt(name, base=base)
    lines = text.splitlines()
    i = 0
    while i < len(lines) and lines[i].strip().startswith("#"):
        i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    return "\n".join(lines[i:]).strip()
