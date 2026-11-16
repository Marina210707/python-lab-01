# FindIndex Lab 4: Типи, тести, пакування і CLI

[![CI](https://github.com/Marina210707/python-lab-01/actions/workflows/ci.yml/badge.svg)](https://github.com/Marina210707/python-lab-01/actions/workflows/ci.yml)

## Опис проєкту
Це четверта лабораторна робота з курсу Python. Проєкт є продовженням пошукового рушія `findindex` (інвертований індекс, ранжування TF-IDF/BM25, парсер запитів).

У цій версії (v0.4.0) додано:
- Сувору типізацію (Pyright у режимі `strict`, 0 помилок).
- Покриття тестами (24 тести на Pytest + Hypothesis).
- CLI з використанням `argparse` та логуванням.
- Пакування проєкту через `pyproject.toml` та збірку `wheel`.
- CI/CD через GitHub Actions.

## Встановлення та використання
Проєкт можна встановити з wheel-файлу (лежить у папці `dist/`):
```bash
pip install dist/findindex-0.4.0-py3-none-any.whl