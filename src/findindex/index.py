import collections
import pickle
import json
from .structures import Posting, DocMeta
from .pipeline import read_documents, tokenize


class InvertedIndex:
    def __init__(self):
        # термін -> список Posting
        self.index: dict[str, list[Posting]] = collections.defaultdict(list)
        # doc_id -> DocMeta
        self.doc_meta: dict[int, DocMeta] = {}

    def build(self, data_dir: str):
        """Будує індекс з папки з документами."""
        docs = read_documents(data_dir)

        for doc_id, (file_path, text) in enumerate(docs.items()):
            tokens = tokenize(text)

            # Зберігаємо метадані документа
            title = file_path.split("\\")[-1] if "\\" in file_path else file_path.split("/")[-1]
            self.doc_meta[doc_id] = DocMeta(doc_id=doc_id, title=title, length=len(tokens))

            # Рахуємо частоти слів у цьому документі
            term_freqs = collections.Counter(tokens)

            # Додаємо постинги в індекс
            for term, freq in term_freqs.items():
                self.index[term].append(Posting(doc_id=doc_id, freq=freq))

        # Сортуємо постинги за doc_id
        for term in self.index:
            self.index[term].sort(key=lambda p: p.doc_id)

    def get_postings(self, term: str) -> list[Posting]:
        """Повертає список постингів для терміну."""
        return self.index.get(term, [])

    # --- МЕТОДИ СЕРІАЛІЗАЦІЇ ---

    def save_pickle(self, filepath: str):
        """Зберігає весь об'єкт індексу у бінарний файл."""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_pickle(cls, filepath: str) -> 'InvertedIndex':
        """Завантажує індекс з бінарного файлу."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)

    def save_json(self, filepath: str):
        """Зберігає індекс у JSON."""
        data = {
            "doc_meta": {k: {"doc_id": v.doc_id, "title": v.title, "length": v.length} for k, v in
                         self.doc_meta.items()},
            "index": {term: [{"doc_id": p.doc_id, "freq": p.freq} for p in postings] for term, postings in
                      self.index.items()}
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, filepath: str) -> 'InvertedIndex':
        """Завантажує індекс з JSON і відновлює об'єкти."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        new_index = cls()
        for k, v in data["doc_meta"].items():
            new_index.doc_meta[int(k)] = DocMeta(doc_id=v["doc_id"], title=v["title"], length=v["length"])

        for term, postings in data["index"].items():
            new_index.index[term] = [Posting(doc_id=p["doc_id"], freq=p["freq"]) for p in postings]

        return new_index