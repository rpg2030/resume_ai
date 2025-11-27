def clean_text(text: str) -> str:
    text = text.replace("\n", " ").replace("\t", " ")
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()
