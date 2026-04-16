import re

_STOP_WORDS = {"a", "an", "the", "and", "or", "but", "in", "on", "at",
               "to", "for", "of", "with", "by", "from", "is", "are"}


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def keyword_to_title(keyword: str) -> str:
    """Format a keyword into a readable title."""
    words = keyword.strip().split()
    return " ".join(
        w.capitalize() if i == 0 or w.lower() not in _STOP_WORDS else w.lower()
        for i, w in enumerate(words)
    )
