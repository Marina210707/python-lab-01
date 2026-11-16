import math
from dataclasses import dataclass
from .index import InvertedIndex


@dataclass(order=True)
class SearchResult:
    """
    Результат пошуку. order=True дозволяє сортувати результати за score.
    Зверни увагу: score йде першим, щоб сортування за замовчуванням було за релевантністю.
    """
    score: float
    doc_id: int
    title: str


class Scorer:
    """Базовий клас (протокол) для всіх алгоритмів ранжування."""

    def __init__(self, index: InvertedIndex):
        self.index = index
        self.N = index.num_docs
        self.avgdl = index.avg_doc_length

    def score(self, term: str, doc_id: int) -> float:
        raise NotImplementedError


class TfIdfScorer(Scorer):
    """Алгоритм TF-IDF."""

    def score(self, term: str, doc_id: int) -> float:
        postings = self.index.get_postings(term)
        # Знаходимо частоту терміну в документі (TF)
        tf = 0
        for p in postings:
            if p.doc_id == doc_id:
                tf = p.freq
                break

        if tf == 0:
            return 0.0

        # Обчислюємо IDF (Inverse Document Frequency)
        df = len(postings)
        idf = math.log((self.N + 1) / (df + 1)) + 1  # Згладжений IDF

        # Повертаємо TF * IDF
        return tf * idf


class BM25Scorer(Scorer):
    """Алгоритм BM25 (кращий за TF-IDF для довгих документів)."""

    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75):
        super().__init__(index)
        self.k1 = k1
        self.b = b

    def score(self, term: str, doc_id: int) -> float:
        postings = self.index.get_postings(term)
        tf = 0
        for p in postings:
            if p.doc_id == doc_id:
                tf = p.freq
                break

        if tf == 0:
            return 0.0

        df = len(postings)
        idf = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

        # Довжина поточного документа
        doc_len = self.index.doc_meta[doc_id].length

        # Формула BM25
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))

        return idf * (numerator / denominator)