import re
import string
from pathlib import Path


def tokenize(text: str) -> list[str]:
    """Розбиває текст на токени (слова) у нижньому регістрі."""
    # Проста токенізація за допомогою регулярних виразів
    # Знаходимо всі послідовності літер та цифр
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def read_documents(data_dir: str) -> dict[str, str]:
    """Читає всі .txt файли з папки і повертає словник {шлях_до_файлу: текст}."""
    docs = {}
    path = Path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Директорія {data_dir} не знайдена.")

    for file_path in path.glob("*.txt"):
        try:
            text = file_path.read_text(encoding="utf-8")
            docs[str(file_path)] = text
        except Exception as e:
            print(f"Помилка читання файлу {file_path}: {e}")
    return docs