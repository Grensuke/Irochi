# ==================================================
# Irochi Backend — Dockerfile (Dummy Phase)
# ==================================================
# Minimal FastAPI dummy-app container.
# Matches docker-compose.yml expectations:
#   - Port 8000
#   - uvicorn with --reload for development
#
# This Dockerfile is for the DUMMY backend only.
# Production concerns (multi-stage builds, non-root
# users, health checks, etc.) will be added later.
# ==================================================

FROM python:3.12.10-slim

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

# Expose the backend port
EXPOSE 8000

# Default command — overridden by docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
