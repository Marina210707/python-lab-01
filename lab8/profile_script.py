import cProfile
import pstats
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from findindex.index import InvertedIndex


def run_build():
    idx = InvertedIndex()
    idx.build("data")


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    run_build()
    profiler.disable()

    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(5)  # Покаже 5 найповільніших функцій