# --- Stage 1: builder ---
FROM python:3.12-slim AS builder

# Install uv via pip (no external registry needed)
RUN pip install uv

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# --- Stage 2: runtime ---
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Make sure we use the venv's Python
ENV PATH="/app/.venv/bin:$PATH"

# Don't buffer Python output (see logs immediately)
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
