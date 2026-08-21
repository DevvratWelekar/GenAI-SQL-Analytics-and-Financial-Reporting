FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OLLAMA_MODEL=qwen2.5:1.5b \
    OLLAMA_HOST=127.0.0.1:11434

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://ollama.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

COPY data ./data
COPY src ./src
RUN python data/generate_data.py
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8501
CMD ["./start.sh"]
