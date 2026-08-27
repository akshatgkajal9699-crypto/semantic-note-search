FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OLLAMA_URL="http://127.0.0.1:11434"

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
