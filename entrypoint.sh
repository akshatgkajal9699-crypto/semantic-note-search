#!/bin/sh
ollama serve &
sleep 5
ollama pull nomic-embed-text
python3 ingest.py
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
