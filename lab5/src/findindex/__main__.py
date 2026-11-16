from .index import InvertedIndex
from .search import Searcher
from .snippet import make_snippet
from .utils import open_index

if __name__ == "__main__":
    print("Будуємо індекс...")
    idx = InvertedIndex()
    idx.build("data")

    # Зберігаємо для тесту open_index
    idx.save_pickle("my_index.pkl")

    query = "мова AND програмування"
    print(f"\nШукаємо: {query}")

    searcher = Searcher(idx, scorer_name="bm25")
    results = searcher.search(query, top_k=3)

    for res in results:
        print(f"\nScore: {res.score:.4f} | Doc ID: {res.doc_id} | Назва: {res.title}")
        # Витягуємо текст документа для сніпета
        from pathlib import Path

        doc_path = Path("data") / res.title
        if doc_path.exists():
            text = doc_path.read_text(encoding="utf-8")
            snippet = make_snippet(text, ["мова", "програмування"])
            print(f"Сніпет: {snippet[:150]}...")  # Обрізаємо для виводу
        else:
            print("Текст документа не знайдено для сніпета.")

    print("\n--- Тест open_index ---")
    with open_index("my_index.pkl") as loaded_idx:
        print(f"Завантажено {loaded_idx.num_docs} документів")