FROM python:3.12-slim AS base

# Development environment Dockerfile (env.dev)

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# System dependencies for psycopg2 and building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Install uv (Python dependency manager used in this project)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && ln -s /root/.local/bin/uv /usr/local/bin/uv

# Copy dependency metadata and install dependencies
COPY pyproject.toml uv.lock ./ 
RUN uv sync --frozen --no-dev

# Copy project source and env file
COPY . .
COPY env.dev ./env.dev

EXPOSE 8050

# Default command: load env.dev and run Django via ASGI with uvicorn
CMD ["sh", "-c", "set -a && . ./env.dev && set +a && uv run uvicorn ugc.asgi:application --host 127.0.0.1 --port 8050"]
