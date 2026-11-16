from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import time
import os
from pathlib import Path

from ..index import InvertedIndex
from ..search import Searcher
from ..snippet import make_snippet

index_instance: Optional[InvertedIndex] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global index_instance
    try:
        index_instance = InvertedIndex.load_pickle("my_index.pkl")
        print("Індекс успішно завантажено.")
    except FileNotFoundError:
        print("Файл індексу не знайдено. Пошук буде недоступний.")
    yield
    index_instance = None


app = FastAPI(lifespan=lifespan)


class SearchResultResponse(BaseModel):
    doc_id: int
    title: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultResponse]


@app.get("/health")
async def health():
    if index_instance is None:
        return JSONResponse(status_code=503, content={"status": "unavailable", "reason": "index not loaded"})
    return {"status": "ok"}


@app.get("/stats")
async def stats():
    if index_instance is None:
        raise HTTPException(status_code=503, detail="Index not loaded")
    return {
        "num_docs": index_instance.num_docs,
        "num_terms": len(index_instance),
        "avg_doc_length": index_instance.avg_doc_length
    }


@app.get("/search", response_model=SearchResponse)
async def search(q: str, scorer: str = "bm25", page: int = 1, size: int = 10):
    if index_instance is None:
        raise HTTPException(status_code=503, detail="Index not loaded")

    searcher = Searcher(index_instance, scorer_name=scorer)
    all_results = searcher.search(q, top_k=100)

    start = (page - 1) * size
    end = start + size
    paginated = all_results[start:end]

    formatted_results = []
    for r in paginated:
        try:
            doc_path = Path("data") / r.title
            text = doc_path.read_text(encoding="utf-8")
            snippet = make_snippet(text, q.split())
        except Exception:
            snippet = "Текст недоступний"

        formatted_results.append(SearchResultResponse(
            doc_id=r.doc_id, title=r.title, score=r.score, snippet=snippet
        ))

    return SearchResponse(query=q, total=len(all_results), results=formatted_results)


@app.get("/docs/{doc_id}")
async def get_doc(doc_id: int):
    if index_instance is None:
        raise HTTPException(status_code=503, detail="Index not loaded")
    if doc_id not in index_instance.doc_meta:
        raise HTTPException(status_code=404, detail="Document not found")

    meta = index_instance.doc_meta[doc_id]
    try:
        doc_path = Path("data") / meta.title
        text = doc_path.read_text(encoding="utf-8")
        return {"doc_id": doc_id, "title": meta.title, "text": text}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not read document")


# --- АВТОМАТИЧНЕ СТВОРЕННЯ ШАБЛОНУ ---
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
os.makedirs(templates_dir, exist_ok=True)

index_html_path = os.path.join(templates_dir, "index.html")
if not os.path.exists(index_html_path):
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>FindIndex Search</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f4f4f4; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] { flex-grow: 1; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; }
        button { padding: 10px 20px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .result { background: white; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .result h3 { margin-top: 0; }
        .score { color: #666; font-size: 12px; }
        .snippet { color: #333; line-height: 1.5; }
    </style>
</head>
<body>
    <h1>Пошук по документах</h1>
    <form method="get" action="/" class="search-box">
        <input type="text" name="q" value="{{ query or '' }}" placeholder="Введіть запит...">
        <button type="submit">Шукати</button>
    </form>

    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}

    {% if results %}
        <p>Знайдено результатів: {{ results|length }}</p>
        {% for r in results %}
            <div class="result">
                <h3>{{ r.title }}</h3>
                <div class="score">Score: {{ "%.4f"|format(r.score) }} | Doc ID: {{ r.doc_id }}</div>
                <div class="snippet">{{ r.title }}</div>
            </div>
        {% endfor %}
    {% endif %}
</body>
</html>""")

templates = Jinja2Templates(directory=templates_dir)


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request, q: Optional[str] = None):
    if not q:
        return templates.TemplateResponse("index.html", {"request": request, "results": None})

    if index_instance is None:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Індекс не завантажено"})

    searcher = Searcher(index_instance, scorer_name="bm25")
    results = searcher.search(q, top_k=10)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "query": q,
        "results": results
    })