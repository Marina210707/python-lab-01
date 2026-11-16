from .index import InvertedIndex
from .structures import Posting


class Searcher:
    def __init__(self, index: InvertedIndex, engine: str = "merge"):
        self.index = index
        # engine може бути "merge" (через списки) або "set" (через множини)
        self.engine = engine

    def search(self, query: str) -> list[int]:
        """
        Головна функція пошуку. Розбирає запит і повертає список doc_id.
        Підтримує прості запити: "word1 AND word2", "word1 OR word2", "word1 NOT word2"
        """
        query = query.lower().strip()
        if not query:
            return []

        # Розбиваємо запит на слова
        parts = query.split()

        # Якщо одне слово
        if len(parts) == 1:
            return self._get_docs_for_term(parts[0])

        # Якщо є оператори (очікуємо формат: слово ОПЕРАТОР слово)
        if len(parts) == 3:
            term1, operator, term2 = parts
            if operator == "and":
                return self._and(term1, term2)
            elif operator == "or":
                return self._or(term1, term2)
            elif operator == "not":
                return self._not(term1, term2)

        # Якщо запит складніший, поки повертаємо пустий список
        print(f"Попередження: Складний запит '{query}' не підтримується.")
        return []

    def _get_docs_for_term(self, term: str) -> list[int]:
        """Повертає список doc_id для одного терміну."""
        postings = self.index.get_postings(term)
        return [p.doc_id for p in postings]

    def _and(self, term1: str, term2: str) -> list[int]:
        """Логіка AND (перетин)."""
        if self.engine == "set":
            return self._and_set(term1, term2)
        else:
            return self._and_merge(term1, term2)

    def _or(self, term1: str, term2: str) -> list[int]:
        """Логіка OR (об'єднання)."""
        if self.engine == "set":
            return self._or_set(term1, term2)
        else:
            return self._or_merge(term1, term2)

    def _not(self, term1: str, term2: str) -> list[int]:
        """Логіка NOT (віднімання: term1 І НЕ term2)."""
        if self.engine == "set":
            return self._not_set(term1, term2)
        else:
            return self._not_merge(term1, term2)

    # --- АЛГОРИТМИ ЧЕРЕЗ MERGE (СПИСКИ) ---
    # Вони працюють швидше, бо списки вже відсортовані за doc_id

    def _and_merge(self, term1: str, term2: str) -> list[int]:
        p1 = self.index.get_postings(term1)
        p2 = self.index.get_postings(term2)
        result = []
        i, j = 0, 0

        # Класичний алгоритм злиття двох відсортованих масивів
        while i < len(p1) and j < len(p2):
            if p1[i].doc_id == p2[j].doc_id:
                result.append(p1[i].doc_id)
                i += 1
                j += 1
            elif p1[i].doc_id < p2[j].doc_id:
                i += 1
            else:
                j += 1
        return result

    def _or_merge(self, term1: str, term2: str) -> list[int]:
        p1 = self.index.get_postings(term1)
        p2 = self.index.get_postings(term2)
        result = []
        i, j = 0, 0

        while i < len(p1) and j < len(p2):
            if p1[i].doc_id == p2[j].doc_id:
                result.append(p1[i].doc_id)
                i += 1
                j += 1
            elif p1[i].doc_id < p2[j].doc_id:
                result.append(p1[i].doc_id)
                i += 1
            else:
                result.append(p2[j].doc_id)
                j += 1

        # Додаємо залишки, якщо один список закінчився раніше
        while i < len(p1):
            result.append(p1[i].doc_id)
            i += 1
        while j < len(p2):
            result.append(p2[j].doc_id)
            j += 1

        return result

    def _not_merge(self, term1: str, term2: str) -> list[int]:
        p1 = self.index.get_postings(term1)
        p2 = self.index.get_postings(term2)
        result = []
        i, j = 0, 0

        # Беремо з p1 тільки те, чого немає в p2
        while i < len(p1) and j < len(p2):
            if p1[i].doc_id == p2[j].doc_id:
                i += 1
                j += 1
            elif p1[i].doc_id < p2[j].doc_id:
                result.append(p1[i].doc_id)
                i += 1
            else:
                j += 1

        # Якщо p2 закінчився, а в p1 ще щось є - додаємо
        while i < len(p1):
            result.append(p1[i].doc_id)
            i += 1

        return result

    # --- АЛГОРИТМИ ЧЕРЕЗ SET (МНОЖИНИ) ---
    # Простіші у написанні, але можуть бути повільнішими на великих даних

    def _and_set(self, term1: str, term2: str) -> list[int]:
        set1 = set(self._get_docs_for_term(term1))
        set2 = set(self._get_docs_for_term(term2))
        return sorted(list(set1.intersection(set2)))

    def _or_set(self, term1: str, term2: str) -> list[int]:
        set1 = set(self._get_docs_for_term(term1))
        set2 = set(self._get_docs_for_term(term2))
        return sorted(list(set1.union(set2)))

    def _not_set(self, term1: str, term2: str) -> list[int]:
        set1 = set(self._get_docs_for_term(term1))
        set2 = set(self._get_docs_for_term(term2))
        return sorted(list(set1.difference(set2)))