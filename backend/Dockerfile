# Backend Dockerfile for FastAPI app
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3

WORKDIR /app

# (Slimmed) No system build deps required now that Postgres removed and all wheels prebuilt.

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Expose port
EXPOSE 8000

# Run directly with uvicorn (lighter, gunicorn not installed). Adjust workers via UVICORN_WORKERS env if desired.
ENV UVICORN_WORKERS=2
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
