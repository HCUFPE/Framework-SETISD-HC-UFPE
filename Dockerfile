# ============================
# 1. FRONTEND - BUILD (VUE 3)
# ============================
FROM node:20 AS frontend-build
WORKDIR /app

# Copia estrutura para o build do frontend gerar arquivos em /src/static/dist
COPY src ./src
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

COPY frontend ./frontend
RUN cd frontend && npm run build

# ============================
# 2. BACKEND & RUNTIME FINAL
# ============================
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Dependências do sistema necessárias para LDAP/AD, PostgreSQL e compilação de pacotes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte do backend e migrações
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini .

# Copia o build estático do frontend gerado no estágio 1
COPY --from=frontend-build /app/src/static/dist ./src/static/dist

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
