FROM python:3.12-slim

WORKDIR /app

# Install system deps for XGBoost / scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Cloud Run injects $PORT (8080); fall back to 8000 for local docker runs
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
