import time
import functools
from typing import Callable, Any, TypeVar, Generator
from contextlib import contextmanager

F = TypeVar('F', bound=Callable[..., Any])


def timed(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"[@timed] {func.__name__} виконано за {end - start:.4f} сек.")
        return result

    return wrapper  # type: ignore


@contextmanager
def open_index(path: str) -> Generator[Any, None, None]:
    # Імпорт всередині функції, щоб уникнути циклічної залежності
    from .index import InvertedIndex

    print(f"Відкриваємо індекс з {path}...")
    idx = InvertedIndex.load_pickle(path)
    try:
        yield idx
    finally:
        print("Закриваємо індекс (звільняємо ресурси)...")