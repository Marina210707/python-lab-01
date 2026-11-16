import argparse
import time
from .index import InvertedIndex
from .search import Searcher


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI для інвертованого індексу")
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")

    # Команда build (побудова)
    build_parser = subparsers.add_parser("build", help="Побудувати та зберегти індекс")
    build_parser.add_argument("data_dir", type=str, help="Шлях до папки з документами")
    build_parser.add_argument("--out", type=str, default="index.pkl", help="Файл для збереження")
    build_parser.add_argument("--format", type=str, choices=["pickle", "json"], default="pickle")

    # Команда search (пошук)
    search_parser = subparsers.add_parser("search", help="Завантажити індекс і шукати")
    search_parser.add_argument("index_file", type=str, help="Шлях до збереженого індексу")
    search_parser.add_argument("query", type=str, help="Пошуковий запрос")
    search_parser.add_argument("--scorer", type=str, choices=["tfidf", "bm25"], default="bm25",
                               help="Алгоритм ранжування")
    search_parser.add_argument("--format", type=str, choices=["pickle", "json"], default="pickle")

    args = parser.parse_args()

    if args.command == "build":
        start_time = time.time()
        idx = InvertedIndex()
        idx.build(args.data_dir)

        if args.format == "pickle":
            idx.save_pickle(args.out)
        else:
            idx.save_json(args.out)

        elapsed = time.time() - start_time
        print(f"Індекс побудовано та збережено у {args.out} за {elapsed:.2f} сек.")
        print(f"Документів: {len(idx.doc_meta)}")

    elif args.command == "search":
        start_load = time.time()
        if args.format == "pickle":
            idx = InvertedIndex.load_pickle(args.index_file)
        else:
            idx = InvertedIndex.load_json(args.index_file)
        load_time = time.time() - start_load

        # Використовуємо scorer_name, як у нашому Searcher
        searcher = Searcher(idx, scorer_name=args.scorer)
        start_search = time.time()
        results = searcher.search(args.query)
        search_time = time.time() - start_search

        print(f"Час завантаження: {load_time:.4f} сек.")
        print(f"Час пошуку: {search_time:.4f} сек.")
        print(f"Знайдено документів: {len(results)}")
        print(f"ID документів: {[r.doc_id for r in results[:10]]}...")


if __name__ == "__main__":
    main()