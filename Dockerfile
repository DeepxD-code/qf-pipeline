FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY apps/api/src ./apps/api/src
COPY packages ./packages
COPY apps/web ./apps/web
COPY scripts ./scripts
RUN pip install --upgrade pip && pip install -e "."

ENV STORAGE_DIR=/app/storage API_PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn qf_api.main:app --host 0.0.0.0 --port ${PORT:-${API_PORT:-8000}}"]
