import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="pgvector Recipe Recommender")

# Initialize OpenAI client and DB URL from Railway environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

class SearchQuery(BaseModel):
    prompt: str
    top_k: int = 3

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.post("/recommend")
def recommend_recipes(query: SearchQuery):
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not set")

    # 1. Convert user's plain language text prompt into a vector
    try:
        response = client.embeddings.create(
            input=query.prompt,
            model="text-embedding-3-small"
        )
        query_vector = response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    # 2. Perform Cosine Similarity Search in pgvector
    conn = get_db_connection()
    cur = conn.cursor()

    # The `<=>` operator computes cosine distance (1 - cosine similarity)
    sql = """
        SELECT id, title, description, (embedding <=> %s::vector) AS distance
        FROM recipes
        ORDER BY distance ASC
        LIMIT %s;
    """

    cur.execute(sql, (str(query_vector), query.top_k))
    results = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "user_query": query.prompt,
        "recommendations": results
    }
