import collections
import pickle
import json
from functools import cached_property
from .structures import Posting, DocMeta
from .pipeline import read_documents, tokenize
from .utils import timed

class InvertedIndex:
    def __init__(self):
        self.index: dict[str, list[Posting]] = collections.defaultdict(list)
        self.doc_meta: dict[int, DocMeta] = {}

    @timed
    def build(self, data_dir: str):
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

    def get_postings(self, term: str) -> list[Posting]:
        return self.index.get(term, [])

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, term: str) -> list[Posting]:
        return self.index.get(term, [])

    def __contains__(self, term: str) -> bool:
        return term in self.index

    def __iter__(self):
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

    def save_pickle(self, filepath: str):
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_pickle(cls, filepath: str) -> 'InvertedIndex':
        with open(filepath, 'rb') as f:
            return pickle.load(f)

    def save_json(self, filepath: str):
        data = {
            "doc_meta": {k: {"doc_id": v.doc_id, "title": v.title, "length": v.length} for k, v in self.doc_meta.items()},
            "index": {term: [{"doc_id": p.doc_id, "freq": p.freq} for p in postings] for term, postings in self.index.items()}
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