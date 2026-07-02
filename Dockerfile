FROM node:22-alpine AS web-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE=/api
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/global_equity_council.db
WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/app /app/backend/app
RUN pip install --no-cache-dir /app/backend
COPY --from=web-build /app/frontend/dist /app/frontend-dist
RUN useradd --create-home --uid 10001 council && mkdir /data && chown council:council /data
USER council
EXPOSE 8000
WORKDIR /app/backend
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
