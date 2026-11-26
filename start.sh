#!/bin/bash

# Cores para o output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   🚀 Iniciando Aplicação                         ${NC}"
echo -e "${BLUE}==================================================${NC}"

# 0. Limpeza de processos anteriores (Linux/macOS e Windows)
echo -e "${YELLOW}🧹 Limpando processos anteriores...${NC}"
if command -v pkill &> /dev/null; then
    pkill -f "uvicorn src.main:app" 2>/dev/null || true
elif command -v powershell.exe &> /dev/null; then
    powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -like '*uvicorn src.main:app*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" 2>/dev/null || true
fi

# 1. Verificação das ferramentas necessárias
echo -e "\n${YELLOW}[1/6] Verificando ferramentas do sistema...${NC}"
tools=("node" "npm" "uv")
for tool in "${tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo -e "${RED}❌ Erro: '$tool' não foi encontrado.${NC}"
        echo -e "Certifique-se de que o ambiente está configurado corretamente."
        exit 1
    else
        version=$($tool --version 2>&1 | head -n 1)
        echo -e "  ✅ $tool:${GREEN}$version${NC}"
    fi
done

# Detecta Python válido (ignora o atalho falso da Microsoft Store no Windows)
PYTHON_BIN=""
for candidate in ".venv/Scripts/python.exe" ".venv/bin/python" "python3" "python"; do
    if version=$($candidate --version 2>/dev/null | head -n 1); then
        PYTHON_BIN="$candidate"
        echo -e "  ✅ python ($candidate):${GREEN}$version${NC}"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "  ⚠️  Python global não encontrado; o ${GREEN}uv${NC} gerenciará o interpretador."
fi

# 2. Criação do venv e 3. Instalação de pacotes Python (via uv)
echo -e "\n${YELLOW}[2-3/6] Sincronizando ambiente Python (uv)...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "  ⚙️  Criando novo ambiente virtual (.venv)..."
fi

if uv sync; then
    echo -e "  ✅ Dependências Python sincronizadas."
else
    echo -e "${RED}❌ Erro ao sincronizar dependências Python.${NC}"
    exit 1
fi

# 4. Instalação das dependências do frontend
echo -e "\n${YELLOW}[4/6] Verificando dependências do frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    if npm install; then
        echo -e "  ✅ Dependências do frontend instaladas."
    else
        echo -e "${RED}❌ Erro ao instalar dependências do frontend.${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Diretório 'frontend' não encontrado.${NC}"
    exit 1
fi

# 5. Build do frontend
echo -e "\n${YELLOW}[5/6] Gerando build do frontend...${NC}"
if npm run build; then
    echo -e "  ✅ Build finalizado com sucesso."
else
    echo -e "${RED}❌ Erro no build do frontend.${NC}"
    exit 1
fi
cd ..

# 6. Migrações do banco de dados
echo -e "\n${YELLOW}[6/6] Aplicando migrações do banco (Alembic)...${NC}"
if uv run alembic upgrade head; then
    echo -e "  ✅ Banco de dados atualizado."
else
    echo -e "${RED}❌ Erro ao executar migrações do Alembic.${NC}"
    exit 1
fi

# Execução da aplicação em foreground
IP="0.0.0.0"
PORT="${PORT:-8000}"
echo -e "\n${GREEN}✅ Aplicação disponível em http://localhost:${PORT}${NC}"
exec uv run uvicorn src.main:app --host "$IP" --port "$PORT"