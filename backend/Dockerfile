# ==================================================
# Vibhinetra Backend — Dockerfile
# ==================================================

FROM python:3.12.10-slim

# Create a non-root user
RUN groupadd -r vibhinetra && useradd -r -g vibhinetra vibhinetra

# Prevent Python from writing .pyc files and enable
# unbuffered stdout/stderr for container logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R vibhinetra:vibhinetra /app
USER vibhinetra

# Expose the backend port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Default command — runs database migrations then starts the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
