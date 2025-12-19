# ============================
# 1. FRONTEND - DEV (VITE)
# ============================
FROM node:20 AS frontend-dev
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ============================
# 2. FRONTEND - BUILD
# ============================
FROM node:20 AS frontend-build
WORKDIR /app

# Backend precisa existir para o Vite colocar assets em /src/static/dist
COPY src ./src

# Frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

COPY frontend ./frontend
RUN cd frontend && npm run build


# ============================
# 3. BACKEND - BUILDER
# ============================
FROM python:3.10-slim AS backend-build
WORKDIR /app

# Dependências necessárias para compilar python-ldap e outras libs nativas
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libpq-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ============================
# 4. BACKEND - RUNTIME FINAL
# ============================
FROM python:3.10-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# libs necessárias para python-ldap funcionar NO RUNTIME
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Backend source
COPY src ./src
COPY requirements.txt .

# Instalando libs Python no runtime
RUN pip install --no-cache-dir -r requirements.txt

# Criar diretório static se não existir
RUN mkdir -p ./src/static/dist

# Copiando o build do frontend para dentro da pasta estática
COPY --from=frontend-build /app/frontend/dist ./src/static/dist

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
