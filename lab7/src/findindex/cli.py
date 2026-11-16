import argparse
import time
import asyncio
import logging
from .index import InvertedIndex
from .search import Searcher
from .crawler import AsyncCrawler

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI для інвертованого індексу")
    subparsers = parser.add_subparsers(dest="command", help="Доступні команди")

    # Команда build
    build_parser = subparsers.add_parser("build", help="Побудувати та зберегти індекс")
    build_parser.add_argument("data_dir", type=str, help="Шлях до папки з документами")
    build_parser.add_argument("--out", type=str, default="index.pkl", help="Файл для збереження")
    build_parser.add_argument("--format", type=str, choices=["pickle", "json"], default="pickle")
    build_parser.add_argument("--workers", type=int, default=1, help="Кількість воркерів")
    build_parser.add_argument("--executor", type=str, choices=["serial", "threads", "processes"], default="serial")

    # Команда search
    search_parser = subparsers.add_parser("search", help="Завантажити індекс і шукати")
    search_parser.add_argument("index_file", type=str, help="Шлях до збереженого індексу")
    search_parser.add_argument("query", type=str, help="Пошуковий запрос")
    search_parser.add_argument("--scorer", type=str, choices=["tfidf", "bm25"], default="bm25")
    search_parser.add_argument("--format", type=str, choices=["pickle", "json"], default="pickle")

    # Команда crawl
    crawl_parser = subparsers.add_parser("crawl", help="Асинхронний краулер")
    crawl_parser.add_argument("start_url", type=str, help="Початковий URL")
    crawl_parser.add_argument("--max-pages", type=int, default=50, help="Максимум сторінок")
    crawl_parser.add_argument("--concurrency", type=int, default=5, help="Кількість одночасних запитів")
    crawl_parser.add_argument("--out", type=str, default="crawl_data", help="Папка для збереження текстів")

    # Команда serve (НОВА)
    serve_parser = subparsers.add_parser("serve", help="Запустити веб-сервер")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--workers", type=int, default=1)

    args = parser.parse_args()

    if args.command == "build":
        start_time = time.time()
        idx = InvertedIndex()
        idx.build(args.data_dir, workers=args.workers, executor=args.executor)
        if args.format == "pickle":
            idx.save_pickle(args.out)
        else:
            idx.save_json(args.out)
        print(f"Індекс збережено у {args.out}")

    elif args.command == "search":
        if args.format == "pickle":
            idx = InvertedIndex.load_pickle(args.index_file)
        else:
            idx = InvertedIndex.load_json(args.index_file)
        searcher = Searcher(idx, scorer_name=args.scorer)
        results = searcher.search(args.query)
        print(f"Знайдено документів: {len(results)}")
        for r in results[:10]:
            print(f"Score: {r.score:.4f} | Doc ID: {r.doc_id} | {r.title}")

    elif args.command == "crawl":
        print(f"Запуск краулера на {args.start_url}...")
        crawler = AsyncCrawler([args.start_url], max_pages=args.max_pages, concurrency=args.concurrency)
        asyncio.run(crawler.crawl())

        import os
        os.makedirs(args.out, exist_ok=True)
        for i, (url, text) in enumerate(crawler.results):
            filename = f"page_{i}.txt"
            filepath = os.path.join(args.out, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\n\n{text}")
        print(f"Збережено {len(crawler.results)} сторінок у папку {args.out}")

    elif args.command == "serve":
        import uvicorn
        import sys
        import os
        # Додаємо шлях до src, щоб uvicorn бачив модуль
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        uvicorn.run("findindex.web.app:app", host="0.0.0.0", port=args.port, workers=args.workers)


if __name__ == "__main__":
    main()