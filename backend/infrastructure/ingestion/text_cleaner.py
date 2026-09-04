import re

PAGE_BANNER_RE = re.compile(r"Synthetic training corpus\s*[—-]\s*Domain Copilot Page\s*\d+")

def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = PAGE_BANNER_RE.sub("\n", text)
    text = re.sub(r"^[•\-]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()