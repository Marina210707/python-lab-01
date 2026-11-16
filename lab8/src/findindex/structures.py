from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Posting:
    __slots__ = ('doc_id', 'freq')
    doc_id: int
    freq: int

    def __getstate__(self) -> tuple[int, int]:
        return (self.doc_id, self.freq)

    def __setstate__(self, state: tuple[int, int]) -> None:
        object.__setattr__(self, 'doc_id', state[0])
        object.__setattr__(self, 'freq', state[1])


@dataclass(frozen=True)
class DocMeta:
    __slots__ = ('doc_id', 'title', 'length')
    doc_id: int
    title: str
    length: int

    def __getstate__(self) -> tuple[int, str, int]:
        return (self.doc_id, self.title, self.length)

    def __setstate__(self, state: tuple[int, str, int]) -> None:
        object.__setattr__(self, 'doc_id', state[0])
        object.__setattr__(self, 'title', state[1])
        object.__setattr__(self, 'length', state[2])


# Новий клас для зберігання постингів у NumPy
class NumpyPostings:
    def __init__(self, doc_ids: list[int], freqs: list[int]):
        self.doc_ids = np.array(doc_ids, dtype=np.int32)
        self.freqs = np.array(freqs, dtype=np.int32)

    def __len__(self) -> int:
        return len(self.doc_ids)