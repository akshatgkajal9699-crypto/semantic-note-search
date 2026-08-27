import os
import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel
from fastembed import TextEmbedding

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

print("Loading fastembed model...")
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "Semantic Note Search API is running!"}

@app.post("/search")
def search_notes(request: QueryRequest):
    embeddings = list(model.embed([request.query]))
    query_vector = embeddings[0].tolist()

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT title, description, embedding <-> %s::vector AS distance
        FROM recipes
        ORDER BY distance ASC
        LIMIT 3;
        """,
        (str(query_vector),)
    )
    
    results = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"title": r[0], "description": r[1], "score": float(r[2])}
        for r in results
    ]
