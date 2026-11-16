import os
import re
import time
import unicodedata
import tracemalloc
from collections import Counter


# --- 1. ГЕНЕРАТОР ---
def iter_documents(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                # Читаємо по рядках, щоб не завантажувати весь файл одразу
                text = f.read()
                yield text


# --- 2. ТОКЕНІЗАТОР ---
word_pattern = re.compile(r"\w+")


def tokenize(text):
    text = unicodedata.normalize('NFKC', text)
    text = text.lower()
    words = word_pattern.findall(text)
    return words


# --- 3. РОЗУМНИЙ СПОСІБ (з генератором) ---
def analyze_corpus(folder_path):
    print("\n--- РОЗУМНИЙ СПОСІБ (генератор) ---")
    tracemalloc.start()
    start_time = time.time()

    doc_count = 0
    token_count = 0
    word_freq = Counter()

    for text in iter_documents(folder_path):
        doc_count += 1
        words = tokenize(text)
        token_count += len(words)
        word_freq.update(words)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()

    print(f"Документів: {doc_count}")
    print(f"Токенів: {token_count}")
    print(f"Унікальних слів: {len(word_freq)}")
    print(f"Топ-5 слів (для перевірки): {word_freq.most_common(5)}")
    print(f"Час: {end_time - start_time:.4f} сек")
    print(f"Пікова пам'ять: {peak / 1024 / 1024:.2f} МБ")


# --- 4. ЖАДІБНИЙ СПОСІБ (через список) ---
def analyze_corpus_greedy(folder_path):
    print("\n--- ЖАДІБНИЙ СПОСІБ (список) ---")
    tracemalloc.start()
    start_time = time.time()

    # ПОГАНО: завантажуємо ВСІ тексти в пам'ять одразу
    all_texts = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                all_texts.append(f.read())

    doc_count = len(all_texts)
    token_count = 0
    word_freq = Counter()

    for text in all_texts:
        words = tokenize(text)
        token_count += len(words)
        word_freq.update(words)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    end_time = time.time()

    print(f"Документів: {doc_count}")
    print(f"Токенів: {token_count}")
    print(f"Унікальних слів: {len(word_freq)}")
    print(f"Час: {end_time - start_time:.4f} сек")
    print(f"Пікова пам'ять: {peak / 1024 / 1024:.2f} МБ")


# --- ЗАПУСК ---
if __name__ == "__main__":
    # Отримуємо шлях до папки, де лежить наш файл main.py (це папка src)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Піднімаємося на один рівень вище (в папку my_lab) і заходимо в data
    data_folder = os.path.join(current_dir, "..", "data")

    analyze_corpus(data_folder)
    analyze_corpus_greedy(data_folder)