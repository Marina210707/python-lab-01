import time
import os
import sys

# Додаємо шлях до src, щоб бачити модуль
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from findindex.index import InvertedIndex


def run_bench():
    data_dir = "data"
    workers_list = [1, 2, 4, 8]
    executors = ["serial", "threads", "processes"]

    print(f"{'Executor':<10} | {'Workers':<7} | {'Time (sec)':<10}")
    print("-" * 35)

    for ex in executors:
        for w in workers_list:
            if ex == "serial" and w > 1:
                continue

            idx = InvertedIndex()
            start = time.perf_counter()

            # Тимчасово вимикаємо print, щоб не заважав
            import builtins
            orig_print = builtins.print
            builtins.print = lambda *args, **kwargs: None

            idx.build(data_dir, workers=w, executor=ex)

            builtins.print = orig_print
            elapsed = time.perf_counter() - start

            print(f"{ex:<10} | {w:<7} | {elapsed:.4f}")


if __name__ == "__main__":
    if not os.path.exists("data"):
        print("Помилка: папка data не знайдена.")
        sys.exit(1)
    run_bench()