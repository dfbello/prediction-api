import unicodedata

def normalize_text(text: str):
    # Remove accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    return text.lower().strip()
