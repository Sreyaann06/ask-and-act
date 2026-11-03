import json
import re
from pathlib import Path

KB_PATH = Path(__file__).resolve().parent.parent / "data" / "kb.json"
STOPWORDS = {"a", "an", "the", "is", "are", "do", "does", "i", "my", "me", "how", "what",
             "can", "to", "of", "in", "on", "for", "and", "or", "it", "you", "your", "we"}


def _tokens(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    # strip a trailing 's' so "contacts" matches "contact"
    return {w.rstrip("s") for w in words if w not in STOPWORDS}


def search_knowledge_base(query: str, top_k: int = 3) -> dict:
    """Keyword search over the local FAQ. Never raises."""
    try:
        if not isinstance(query, str) or not query.strip():
            return {"error": "Empty search query"}

        with open(KB_PATH, encoding="utf-8") as f:
            entries = json.load(f)

        q = _tokens(query)
        scored = []
        for e in entries:
            overlap = len(q & _tokens(e["question"] + " " + e["answer"]))
            if overlap:
                scored.append((overlap, e))
        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return {"results": [], "note": "No matching entries found"}
        return {"results": [{"question": e["question"], "answer": e["answer"]}
                            for _, e in scored[:top_k]]}
    except FileNotFoundError:
        return {"error": "Knowledge base file not found"}
    except (json.JSONDecodeError, KeyError):
        return {"error": "Knowledge base file is malformed"}