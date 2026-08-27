import os
import glob
import json
import sqlite3
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = "nomic-embed-text"
DB_FILE = "notes_vectors.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    conn.close()

def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def get_embedding(text):
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": MODEL_NAME, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]

def process_notes():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chunks") # Clear old entries

    files = glob.glob("notes/*.md") + glob.glob("notes/*.txt")
    print(f"Found {len(files)} notes to process.")

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for chunk in chunks:
            embedding = get_embedding(chunk)
            cursor.execute(
                "INSERT INTO chunks (filename, content, embedding) VALUES (?, ?, ?)",
                (filepath, chunk, json.dumps(embedding))
            )
            print(f"Indexed chunk from {filepath}")

    conn.commit()
    conn.close()
    print("Ingestion complete!")

if __name__ == "__main__":
    process_notes()
