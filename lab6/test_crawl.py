import asyncio
import sys
import os
from aiohttp import web

# Додаємо шлях до src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from findindex.crawler import AsyncCrawler


async def handle(request):
    return web.Response(text="<html><body><h1>Test</h1><a href='/page2'>Next</a></body></html>",
                        content_type="text/html")


async def handle_page2(request):
    return web.Response(text="<html><body><h1>Page 2</h1></body></html>", content_type="text/html")


async def main():
    # Запускаємо локальний сервер
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/page2', handle_page2)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    print("Сервер запущено на http://localhost:8080")

    # Запускаємо краулер
    crawler = AsyncCrawler(["http://localhost:8080"], max_pages=5, concurrency=2)
    await crawler.crawl()

    print(f"Зібрано сторінок: {len(crawler.results)}")
    for url, text in crawler.results:
        print(f"URL: {url}")
        print(f"Текст: {text[:50]}...")

    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())