def make_snippet(text: str, query_terms: list[str], window: int = 80) -> str:
    """Знаходить найкраще входження терміну і вирізає шматок тексту навколо нього."""
    text_lower = text.lower()
    best_pos = -1

    # Шукаємо позицію першого знайденого терміну
    for term in query_terms:
        pos = text_lower.find(term.lower())
        if pos != -1:
            best_pos = pos
            break

    if best_pos == -1:
        # Якщо термін не знайдено, повертаємо початок тексту
        return text[:window * 2] + "..."

    start = max(0, best_pos - window)
    end = min(len(text), best_pos + len(query_terms[0]) + window)

    snippet = text[start:end]

    # Додаємо трикрапки, якщо обрізали
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet