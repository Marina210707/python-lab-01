import time
import os
import sys
import tracemalloc

# Додаємо шлях до src, щоб бачити наш пакет
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from findindex.index import InvertedIndex
from findindex.search import Searcher
from findindex.structures import Posting, DocMeta


def measure_memory():
    print("\n--- 1. ЗАМІР ПАМ'ЯТІ (Memory Usage) ---")
    tracemalloc.start()

    N = 100_000

    # 1. Звичайний dataclass (імітація)
    class PostingNoSlots:
        def __init__(self, doc_id, freq):
            self.doc_id = doc_id
            self.freq = freq

    tracemalloc.reset_peak()
    lst1 = [PostingNoSlots(i, 1) for i in range(N)]
    current, peak = tracemalloc.get_traced_memory()
    print(f"Звичайний клас: {current / 10 ** 6:.2f} MB")
    del lst1

    # 2. Posting з __slots__
    tracemalloc.reset_peak()
    lst2 = [Posting(i, 1) for i in range(N)]
    current, peak = tracemalloc.get_traced_memory()
    print(f"Клас з __slots__: {current / 10 ** 6:.2f} MB")
    del lst2

    tracemalloc.stop()


def measure_merge_vs_set():
    print("\n--- 2. БЕНЧМАРК: MERGE vs SET ---")
    idx = InvertedIndex()
    idx.build("data")

    searcher_merge = Searcher(idx, engine="merge")
    searcher_set = Searcher(idx, engine="set")

    terms = sorted(idx.index.keys(), key=lambda t: len(idx.index[t]), reverse=True)
    if len(terms) < 4:
        print("Мало термінів для тесту.")
        return

    test_terms = terms[:2] + terms[-2:]

    for t1 in test_terms:
        t2 = terms[0]

        start = time.perf_counter()
        searcher_merge.search(f"{t1} and {t2}")
        merge_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        searcher_set.search(f"{t1} and {t2}")
        set_time = (time.perf_counter() - start) * 1000

        print(f"Термін '{t1}' (всього {len(idx.index[t1])} док.): Merge={merge_time:.4f} ms | Set={set_time:.4f} ms")


def measure_save_load():
    print("\n--- 3. БЕНЧМАРК: SAVE / LOAD ---")
    idx = InvertedIndex()
    idx.build("data")

    # Pickle
    start = time.perf_counter()
    idx.save_pickle("bench_index.pkl")
    pickle_save_time = time.perf_counter() - start
    pickle_size = os.path.getsize("bench_index.pkl") / (1024 * 1024)

    start = time.perf_counter()
    InvertedIndex.load_pickle("bench_index.pkl")
    pickle_load_time = time.perf_counter() - start

    print(f"Pickle: Розмір={pickle_size:.2f} MB | Save={pickle_save_time:.4f} с | Load={pickle_load_time:.4f} с")

    # JSON
    start = time.perf_counter()
    idx.save_json("bench_index.json")
    json_save_time = time.perf_counter() - start
    json_size = os.path.getsize("bench_index.json") / (1024 * 1024)

    start = time.perf_counter()
    InvertedIndex.load_json("bench_index.json")
    json_load_time = time.perf_counter() - start

    print(f"JSON:   Розмір={json_size:.2f} MB | Save={json_save_time:.4f} с | Load={json_load_time:.4f} с")


if __name__ == "__main__":
    if not os.path.exists("data"):
        print("Помилка: запускайте скрипт з папки lab2")
        sys.exit(1)

    measure_memory()
    measure_merge_vs_set()
    measure_save_load()