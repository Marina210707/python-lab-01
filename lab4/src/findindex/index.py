import collections
import pickle
import json
from functools import cached_property
from .structures import Posting, DocMeta
from .pipeline import read_documents, tokenize


# Тут ми не імпортуємо utils, щоб не було циклу

class InvertedIndex:
    def __init__(self) -> None:
        self.index: dict[str, list[Posting]] = collections.defaultdict(list)
        self.doc_meta: dict[int, DocMeta] = {}

    def build(self, data_dir: str) -> None:
        # Імпортуємо декоратор всередині методу
        from .utils import timed
        # Оскільки декоратор треба навісити на метод, а ми всередині,
        # простіше викликати його як звичайну функцію-обгортку, або
        # залишити як є, якщо він не критичний.
        # Але для чистоти, давай просто викличемо логіку всередині.
        import time
        start = time.perf_counter()

        docs = read_documents(data_dir)
        for doc_id, (file_path, text) in enumerate(docs.items()):
            tokens = tokenize(text)
            title = file_path.split("\\")[-1] if "\\" in file_path else file_path.split("/")[-1]
            self.doc_meta[doc_id] = DocMeta(doc_id=doc_id, title=title, length=len(tokens))
            term_freqs = collections.Counter(tokens)
            for term, freq in term_freqs.items():
                self.index[term].append(Posting(doc_id=doc_id, freq=freq))
        for term in self.index:
            self.index[term].sort(key=lambda p: p.doc_id)

        end = time.perf_counter()
        print(f"[@timed] build виконано за {end - start:.4f} сек.")

    def get_postings(self, term: str) -> list[Posting]:
        return self.index.get(term, [])

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, term: str) -> list[Posting]:
        return self.index.get(term, [])

    def __contains__(self, term: str) -> bool:
        return term in self.index

    def __iter__(self) -> iter:  # type: ignore
        return iter(self.index)

    def __repr__(self) -> str:
        return f"<InvertedIndex docs={len(self.doc_meta)} terms={len(self.index)}>"

    @cached_property
    def num_docs(self) -> int:
        return len(self.doc_meta)

    @cached_property
    def avg_doc_length(self) -> float:
        if not self.doc_meta:
            return 0.0
        total_length = sum(meta.length for meta in self.doc_meta.values())
        return total_length / len(self.doc_meta)

    def save_pickle(self, filepath: str) -> None:
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_pickle(cls, filepath: str) -> 'InvertedIndex':
        with open(filepath, 'rb') as f:
            return pickle.load(f)

    def save_json(self, filepath: str) -> None:
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
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        new_index = cls()
        for k, v in data["doc_meta"].items():
            new_index.doc_meta[int(k)] = DocMeta(doc_id=v["doc_id"], title=v["title"], length=v["length"])
        for term, postings in data["index"].items():
            new_index.index[term] = [Posting(doc_id=p["doc_id"], freq=p["freq"]) for p in postings]
        return new_index