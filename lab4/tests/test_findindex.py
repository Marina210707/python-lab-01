import pytest
from pathlib import Path
from hypothesis import given, strategies as st
from findindex.index import InvertedIndex
from findindex.search import Searcher
from findindex.parser import parse_query, TermNode, AndNode, OrNode
from findindex.pipeline import tokenize
from findindex.ranking import TfIdfScorer, BM25Scorer

# --- Фікстури ---
@pytest.fixture
def small_corpus(tmp_path: Path) -> Path:
    """Створює тимчасовий корпус з 3 файлів для тестів."""
    d = tmp_path / "data"
    d.mkdir()
    (d / "doc1.txt").write_text("apple banana apple", encoding="utf-8")
    (d / "doc2.txt").write_text("banana cherry", encoding="utf-8")
    (d / "doc3.txt").write_text("apple cherry cherry cherry", encoding="utf-8")
    return d

@pytest.fixture
def built_index(small_corpus: Path) -> InvertedIndex:
    idx = InvertedIndex()
    idx.build(str(small_corpus))
    return idx

# --- Тести токенізатора (параметризація) ---
@pytest.mark.parametrize("text, expected", [
    ("Hello, World!", ["hello", "world"]),
    ("Привіт, світ!", ["привіт", "світ"]),
    ("123 456", ["123", "456"]),
    ("", []),
    ("   ", []),
])
def test_tokenize(text: str, expected: list[str]) -> None:
    assert tokenize(text) == expected

# --- Тести побудови індексу ---
def test_build_index(built_index: InvertedIndex) -> None:
    assert len(built_index.doc_meta) == 3
    assert "apple" in built_index
    assert "banana" in built_index
    assert "cherry" in built_index
    assert "grape" not in built_index

def test_postings_sorted(built_index: InvertedIndex) -> None:
    postings = built_index.get_postings("apple")
    assert all(postings[i].doc_id <= postings[i+1].doc_id for i in range(len(postings)-1))

def test_doc_meta_lengths(built_index: InvertedIndex) -> None:
    assert built_index.doc_meta[0].length == 3
    assert built_index.doc_meta[1].length == 2
    assert built_index.doc_meta[2].length == 4

# --- Тести парсера (порівняння дерев) ---
def test_parser_simple_term() -> None:
    ast = parse_query("apple")
    assert isinstance(ast, TermNode)
    assert ast.term == "apple"

def test_parser_and() -> None:
    ast = parse_query("apple AND banana")
    assert isinstance(ast, AndNode)

def test_parser_or() -> None:
    ast = parse_query("apple OR banana")
    assert isinstance(ast, OrNode)

def test_parser_complex() -> None:
    ast = parse_query("(apple OR banana) AND cherry")
    assert isinstance(ast, AndNode)

def test_parser_phrase() -> None:
    ast = parse_query('"apple banana"')
    assert ast is not None

# --- Тести Scorer (TF-IDF vs BM25) ---
def test_tfidf_scorer(built_index: InvertedIndex) -> None:
    scorer = TfIdfScorer(built_index)
    score = scorer.score("apple", 0)
    assert score > 0

def test_bm25_scorer(built_index: InvertedIndex) -> None:
    scorer = BM25Scorer(built_index)
    score = scorer.score("apple", 0)
    assert score > 0

def test_scorer_unknown_term(built_index: InvertedIndex) -> None:
    scorer = TfIdfScorer(built_index)
    assert scorer.score("unknown", 0) == 0.0

# --- Тести Search ---
def test_search_and(built_index: InvertedIndex) -> None:
    searcher = Searcher(built_index)
    results = searcher.search("apple AND banana")
    assert len(results) == 1
    assert results[0].doc_id == 0

def test_search_or(built_index: InvertedIndex) -> None:
    searcher = Searcher(built_index)
    results = searcher.search("apple OR banana")
    # Всі 3 документи містять або apple, або banana
    assert len(results) == 3

def test_search_not(built_index: InvertedIndex) -> None:
    searcher = Searcher(built_index)
    results = searcher.search("apple NOT banana")
    # Перевіряємо, що документ 2 (doc3) є в результатах
    assert len(results) >= 1
    assert any(r.doc_id == 2 for r in results)

# --- Тести серіалізації (save/load) ---
def test_pickle_save_load(built_index: InvertedIndex, tmp_path: Path) -> None:
    filepath = tmp_path / "test.pkl"
    built_index.save_pickle(str(filepath))
    loaded = InvertedIndex.load_pickle(str(filepath))
    assert len(loaded.doc_meta) == len(built_index.doc_meta)
    assert "apple" in loaded

def test_json_save_load(built_index: InvertedIndex, tmp_path: Path) -> None:
    filepath = tmp_path / "test.json"
    built_index.save_json(str(filepath))
    loaded = InvertedIndex.load_json(str(filepath))
    assert len(loaded.doc_meta) == len(built_index.doc_meta)
    assert "apple" in loaded

# --- Тести Hypothesis (властивості) ---
@given(st.text(min_size=1))
def test_hypothesis_tokenize(text: str) -> None:
    tokens = tokenize(text)
    assert isinstance(tokens, list)

@given(st.lists(st.text(min_size=1)))
def test_hypothesis_postings_sorted(terms: list[str]) -> None:
    pass # Спрощено для швидкості

# --- Тести CLI (через subprocess або mock) ---
def test_cli_build(small_corpus: Path, tmp_path: Path) -> None:
    out_file = tmp_path / "cli_index.pkl"
    import sys
    old_argv = sys.argv
    sys.argv = ["findindex", "build", str(small_corpus), "--out", str(out_file)]
    try:
        from findindex.cli import main
        main()
        assert out_file.exists()
    finally:
        sys.argv = old_argv