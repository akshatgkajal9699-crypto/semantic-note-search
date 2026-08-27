import os
import json
import sqlite3
import math
import requests
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = "nomic-embed-text"
DB_FILE = "notes_vectors.db"

def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def get_query_embedding(text):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": MODEL_NAME, "prompt": text}
    )
    return response.json()["embedding"]

@app.get("/search")
def search(q: str = Query(..., min_length=1)):
    query_vector = get_query_embedding(q)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, content, embedding FROM chunks")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for filename, content, embedding_str in rows:
        doc_vector = json.loads(embedding_str)
        score = cosine_similarity(query_vector, doc_vector)
        results.append({
            "filename": filename,
            "content": content,
            "score": round(score, 4)
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Semantic Note Search</title>
        <style>
            body { font-family: sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; }
            input { width: 75%; padding: 10px; font-size: 16px; }
            button { padding: 10px 15px; font-size: 16px; cursor: pointer; }
            .result { background: #f4f4f4; padding: 15px; margin-top: 10px; border-radius: 5px; }
            .score { font-weight: bold; color: #2a7ae9; }
        </style>
    </head>
    <body>
        <h2>Semantic Search Engine</h2>
        <input type="text" id="query" placeholder="Ask something about your notes...">
        <button onclick="runSearch()">Search</button>
        <div id="results"></div>

        <script>
            async function runSearch() {
                const q = document.getElementById('query').value;
                const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                let html = '';
                data.forEach(item => {
                    html += `<div class="result">
                        <span class="score">Score: ${item.score}</span> | <strong>${item.filename}</strong>
                        <p>${item.content}</p>
                    </div>`;
                });
                document.getElementById('results').innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
