# ==================================================
# Irochi Frontend — Dockerfile (Dummy Phase)
# ==================================================
# Minimal React + Vite development container.
# Matches docker-compose.yml expectations:
#   - Port 5173
#   - npm run dev with --host 0.0.0.0
#
# This Dockerfile is for the DUMMY frontend only.
# Production concerns (multi-stage builds, nginx,
# static asset serving, etc.) will be added later.
# ==================================================

FROM node:22-alpine

WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json ./
RUN npm ci

# Copy application code
COPY . .

# Expose the dev server port
EXPOSE 5173

# Default command — overridden by docker-compose.yml
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
