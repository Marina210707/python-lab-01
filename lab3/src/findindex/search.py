import heapq
from .index import InvertedIndex
from .parser import TermNode, PhraseNode, NotNode, AndNode, OrNode, parse_query
from .ranking import TfIdfScorer, BM25Scorer, SearchResult


class Searcher:
    def __init__(self, index: InvertedIndex, scorer_name: str = "bm25"):
        self.index = index
        # Вибираємо алгоритм ранжування
        if scorer_name.lower() == "tfidf":
            self.scorer = TfIdfScorer(index)
        else:
            self.scorer = BM25Scorer(index)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Головна функція пошуку. Повертає топ-K результатів."""
        ast = parse_query(query)
        if not ast:
            return []

        # Отримуємо список doc_id, які підходять під запит
        matched_docs = self._evaluate(ast)

        if not matched_docs:
            return []

        # Тепер треба порахувати score для кожного знайденого документа
        # Для цього зберемо всі терміни з запиту
        terms = self._extract_terms(ast)

        results = []
        for doc_id in matched_docs:
            total_score = 0.0
            # Сумуємо score для кожного терміну в документі
            for term in terms:
                total_score += self.scorer.score(term, doc_id)

            # Якщо score > 0, додаємо в результати
            if total_score > 0:
                meta = self.index.doc_meta[doc_id]
                results.append(SearchResult(score=total_score, doc_id=doc_id, title=meta.title))

        # Сортуємо результати за спаданням score (найкращі зверху)
        # Використовуємо heapq.nlargest для ефективності
        top_results = heapq.nlargest(top_k, results)
        return top_results

    def _evaluate(self, node) -> set[int]:
        """Рекурсивно обходить дерево і повертає множину doc_id."""
        if isinstance(node, TermNode):
            return set(p.doc_id for p in self.index.get_postings(node.term.lower()))

        elif isinstance(node, PhraseNode):
            # Спрощена логіка для фраз: шукаємо документи, де є всі слова з фрази
            # (У реальній системі тут треба перевіряти позиції, але для лаби зійде)
            words = node.phrase.lower().split()
            if not words: return set()
            result = self._evaluate(TermNode(words[0]))
            for w in words[1:]:
                result = result.intersection(self._evaluate(TermNode(w)))
            return result

        elif isinstance(node, NotNode):
            all_docs = set(self.index.doc_meta.keys())
            operand_docs = self._evaluate(node.operand)
            return all_docs - operand_docs

        elif isinstance(node, AndNode):
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return left.intersection(right)

        elif isinstance(node, OrNode):
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return left.union(right)

        return set()

    def _extract_terms(self, node) -> list[str]:
        """Збирає всі унікальні терміни з дерева запиту для ранжування."""
        if isinstance(node, TermNode):
            return [node.term.lower()]
        elif isinstance(node, PhraseNode):
            return node.phrase.lower().split()
        elif isinstance(node, NotNode):
            return []  # Терміни з NOT не додають балів
        elif isinstance(node, (AndNode, OrNode)):
            return self._extract_terms(node.left) + self._extract_terms(node.right)
        return []