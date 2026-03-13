FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99

WORKDIR /app

RUN apt-get -o Acquire::Retries=3 update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    ca-certificates \
    x11-utils \
    xauth \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/database /app/storage
RUN playwright install-deps chromium \
    && playwright install chromium

EXPOSE 8000

CMD ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
