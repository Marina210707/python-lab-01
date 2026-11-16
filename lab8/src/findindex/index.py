import collections
import pickle
import json
import time
import numpy as np
from functools import cached_property
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from .structures import Posting, DocMeta, NumpyPostings
from .pipeline import read_documents, tokenize


class InvertedIndex:
    def __init__(self) -> None:
        # Тепер index зберігає NumpyPostings, а не список Posting
        self.index: dict[str, NumpyPostings] = {}
        self.doc_meta: dict[int, DocMeta] = {}

    def build_partial(self, file_paths: list[str], start_doc_id: int) -> tuple[
        dict[str, tuple[list[int], list[int]]], dict[int, DocMeta]]:
        partial_index: dict[str, tuple[list[int], list[int]]] = collections.defaultdict(lambda: ([], []))
        partial_meta: dict[int, DocMeta] = {}
        current_doc_id = start_doc_id

        for file_path in file_paths:
            try:
                text = Path(file_path).read_text(encoding="utf-8")
            except Exception:
                continue
            tokens = tokenize(text)
            partial_meta[current_doc_id] = DocMeta(doc_id=current_doc_id, title=Path(file_path).name,
                                                   length=len(tokens))
            term_freqs = collections.Counter(tokens)
            for term, freq in term_freqs.items():
                doc_ids, freqs = partial_index[term]
                doc_ids.append(current_doc_id)
                freqs.append(freq)
            current_doc_id += 1
        return partial_index, partial_meta

    def merge(self, partials: list[tuple[dict[str, tuple[list[int], list[int]]], dict[int, DocMeta]]]) -> None:
        self.index = {}
        self.doc_meta = {}

        # Збираємо всі дані в тимчасові списки
        temp_index: dict[str, tuple[list[int], list[int]]] = collections.defaultdict(lambda: ([], []))

        for partial_index, partial_meta in partials:
            for term, (doc_ids, freqs) in partial_index.items():
                t_ids, t_freqs = temp_index[term]
                t_ids.extend(doc_ids)
                t_freqs.extend(freqs)
            self.doc_meta.update(partial_meta)

        # Конвертуємо в NumPy та сортуємо
        for term, (doc_ids, freqs) in temp_index.items():
            # Сортуємо за doc_id
            sorted_indices = np.argsort(doc_ids)
            sorted_ids = np.array(doc_ids, dtype=np.int32)[sorted_indices]
            sorted_freqs = np.array(freqs, dtype=np.int32)[sorted_indices]
            self.index[term] = NumpyPostings(sorted_ids, sorted_freqs)

    def build(self, data_dir: str, workers: int = 1, executor: str = "serial") -> None:
        start = time.perf_counter()
        docs = read_documents(data_dir)
        file_paths = list(docs.keys())

        if not file_paths:
            print("Немає файлів для обробки.")
            return

        chunk_size = max(1, len(file_paths) // workers)
        chunks = [file_paths[i:i + chunk_size] for i in range(0, len(file_paths), chunk_size)]

        partials = []

        if executor == "serial" or workers == 1:
            for i, chunk in enumerate(chunks):
                partials.append(self.build_partial(chunk, i * chunk_size))
        elif executor == "threads":
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(self.build_partial, chunk, i * chunk_size) for i, chunk in enumerate(chunks)]
                for f in as_completed(futures):
                    partials.append(f.result())
        elif executor == "processes":
            with ProcessPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(self.build_partial, chunk, i * chunk_size) for i, chunk in enumerate(chunks)]
                for f in as_completed(futures):
                    partials.append(f.result())

        self.merge(partials)
        end = time.perf_counter()
        print(f"[@timed] build ({executor}, {workers} workers) виконано за {end - start:.4f} сек.")

    def get_postings(self, term: str) -> NumpyPostings:
        return self.index.get(term, NumpyPostings([], []))

    def __len__(self) -> int:
        return len(self.index)

    def __getitem__(self, term: str) -> NumpyPostings:
        return self.index.get(term, NumpyPostings([], []))

    def __contains__(self, term: str) -> bool:
        return term in self.index

    def __iter__(self) -> iter:
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