FROM python:3.10-slim

# Install curl and download the compiled Ollama binary directly
RUN apt-get update && apt-get install -y curl && \
    curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/usr/local/bin/ollama || \
    curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama && \
    chmod +x /usr/local/bin/ollama

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OLLAMA_URL="http://127.0.0.1:11434"

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
