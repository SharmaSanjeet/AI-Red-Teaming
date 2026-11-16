# Nova — Samr VULNERABLE TRAINING TARGET (local lab use only)
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Defaults: stub LLM unless an Ollama service is reachable; unhardened.
ENV OLLAMA_URL=http://ollama:11434 \
    OLLAMA_MODEL=qwen2.5:3b \
    SAMR_HARDENED=0

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
