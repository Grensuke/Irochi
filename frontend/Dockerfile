# ==================================================
# Vibhinetra Frontend — Dockerfile
# ==================================================

# --------------------------------------------------
# Stage 1: Development / Base
# --------------------------------------------------
FROM node:22-alpine as dev
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --------------------------------------------------
# Stage 2: Build
# --------------------------------------------------
FROM dev as builder
RUN npm run build

# --------------------------------------------------
# Stage 3: Production Server (nginx)
# --------------------------------------------------
FROM nginx:alpine as production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:80/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
