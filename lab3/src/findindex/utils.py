import time
import functools
from contextlib import contextmanager
# Імпорт всередині функції, щоб уникнути циклічної залежності
# from .index import InvertedIndex

def timed(func):
    """Декоратор, який вимірює час виконання функції."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"[@timed] {func.__name__} виконано за {end - start:.4f} сек.")
        return result
    return wrapper

@contextmanager
def open_index(path: str):
    """
    Контекстний менеджер для завантаження індексу.
    Використання: with open_index("my_index.pkl") as idx: ...
    """
    from .index import InvertedIndex  # Імпорт тут, щоб уникнути циклу
    print(f"Відкриваємо індекс з {path}...")
    idx = InvertedIndex.load_pickle(path)
    try:
        yield idx
    finally:
        print("Закриваємо індекс (звільняємо ресурси)...")