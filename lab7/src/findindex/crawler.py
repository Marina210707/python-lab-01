import asyncio
import aiohttp
import logging
from urllib.parse import urlparse, urljoin
from selectolax.lexbor import LexborHTMLParser  # <--- ВИПРАВЛЕНО ТУТ
from typing import Set, List, Tuple

logger = logging.getLogger(__name__)


class AsyncCrawler:
    def __init__(self, start_urls: List[str], max_pages: int = 100, concurrency: int = 5):
        self.start_urls = start_urls
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.seen: Set[str] = set()
        self.results: List[Tuple[str, str]] = []  # (url, text)
        self.semaphore = asyncio.Semaphore(concurrency)
        self.pages_crawled = 0

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        # Схема і хост у нижньому регістрі, відкидаємо фрагмент
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path}"

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, str, int]:
        """Завантажує сторінку. Повертає (url, текст, статус)."""
        async with self.semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return url, html, 200
                    elif response.status in (429, 500, 502, 503, 504):
                        logger.warning(f"Помилка {response.status} на {url}. Пропускаємо.")
                        return url, "", response.status
                    else:
                        return url, "", response.status
            except asyncio.TimeoutError:
                logger.error(f"Таймаут на {url}")
                return url, "", 408
            except Exception as e:
                logger.error(f"Помилка на {url}: {e}")
                return url, "", 500

    async def crawl(self):
        """Головний цикл краулера."""
        async with aiohttp.ClientSession() as session:
            queue = asyncio.Queue()
            for url in self.start_urls:
                await queue.put(url)
                self.seen.add(self._normalize_url(url))

            async def worker():
                while self.pages_crawled < self.max_pages:
                    try:
                        url = await asyncio.wait_for(queue.get(), timeout=2.0)
                    except asyncio.TimeoutError:
                        break

                    url, html, status = await self.fetch(session, url)

                    if status == 200 and html:
                        self.pages_crawled += 1
                        logger.info(f"[{self.pages_crawled}/{self.max_pages}] Оброблено: {url}")

                        tree = LexborHTMLParser(html)  # <--- ВИПРАВЛЕНО ТУТ
                        text = tree.body.text() if tree.body else ""
                        self.results.append((url, text))

                        for a in tree.css("a"):
                            href = a.attributes.get("href")
                            if href:
                                full_url = urljoin(url, href)
                                norm_url = self._normalize_url(full_url)
                                if norm_url.startswith(self._normalize_url(self.start_urls[0])):
                                    if norm_url not in self.seen:
                                        self.seen.add(norm_url)
                                        await queue.put(full_url)

                    queue.task_done()

            tasks = [asyncio.create_task(worker()) for _ in range(self.concurrency)]
            await asyncio.gather(*tasks)

        logger.info(f"Краулінг завершено. Зібрано сторінок: {len(self.results)}")