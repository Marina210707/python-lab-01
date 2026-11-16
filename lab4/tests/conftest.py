import sys
import os

# Додаємо папку src до шляху пошуку модулів
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))