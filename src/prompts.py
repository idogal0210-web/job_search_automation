"""Prompt template loader for job evaluation and CV tailoring."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT_DIR / "prompts"

_PROMPT_CACHE = {}


def get_prompt_template(filename: str) -> str:
    """Load and cache prompt template string from prompts directory."""
    if filename in _PROMPT_CACHE:
        return _PROMPT_CACHE[filename]
    path = PROMPTS_DIR / filename
    if path.exists():
        text = path.read_text(encoding="utf-8")
        _PROMPT_CACHE[filename] = text
        return text
    raise FileNotFoundError(f"Prompt template not found: {path}")
