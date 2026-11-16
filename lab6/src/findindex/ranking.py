import math
from dataclasses import dataclass
from typing import Protocol
from .index import InvertedIndex

@dataclass(order=True)
class SearchResult:
    score: float
    doc_id: int
    title: str

class ScorerProtocol(Protocol):
    """Протокол для алгоритмів ранжування (duck typing)."""
    def score(self, term: str, doc_id: int) -> float: ...

class TfIdfScorer:
    def __init__(self, index: InvertedIndex):
        self.index = index
        self.N = index.num_docs

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
        idf = math.log((self.N + 1) / (df + 1)) + 1
        return tf * idf

class BM25Scorer:
    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.N = index.num_docs
        self.avgdl = index.avg_doc_length
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
        doc_len = self.index.doc_meta[doc_id].length
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
        return idf * (numerator / denominator)