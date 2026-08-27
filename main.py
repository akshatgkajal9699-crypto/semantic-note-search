import os
import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastembed import TextEmbedding

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

# Load model globally on server boot
model = None

@app.on_event("startup")
def load_model():
    global model
    print("Pre-loading fastembed model on startup...")
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    print("Model loaded successfully!")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "Semantic Note Search API is running!"}

@app.post("/search")
def search_notes(request: QueryRequest):
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL environment variable is missing.")
    
    if model is None:
        raise HTTPException(status_code=500, detail="Embedding model is not ready.")

    try:
        # Generate 384-dim vector
        embeddings = list(model.embed([request.query]))
        query_vector = embeddings[0].tolist()

        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Execute cosine similarity search
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
