# Stage 1: Build Frontend (Vue 3 + Vite)
FROM node:20-alpine AS builder-frontend
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + Final Runtime Image
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências de sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copiar código do backend
COPY backend /app/backend

# Copiar os arquivos compilados do frontend para a pasta estática do FastAPI
COPY --from=builder-frontend /app/backend/src/static/dist /app/backend/src/static/dist

# Criar diretório de dados para o SQLite
RUN mkdir -p /app/backend/data

WORKDIR /app/backend

EXPOSE 8000

# Script de entrada: roda migrations com Alembic e inicia uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
