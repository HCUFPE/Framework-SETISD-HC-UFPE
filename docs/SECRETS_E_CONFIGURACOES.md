# Padrão de Configurações e Gestão de Segredos (Env Vars & Secrets)
> **Norma Técnica de Governança de Configurações e Criptografia**  
> *Hospital das Clínicas da UFPE (HC-UFPE / EBSERH)*

---

## 🏛️ 1. Princípios Fundamentais

Para garantir a **segurança da informação corporativa** e a **padronização arquitetural** em todos os sistemas desenvolvidos no HC-UFPE, a gestão de variáveis de ambiente deve seguir os seguintes princípios:

1. **Separação Estrita de Código e Configuração:** NENHUMA senha, chave de API, DSN de banco ou credencial de serviço pode ser gravada diretamente no código-fonte Python ou TypeScript (*hardcoded*).
2. **Isolamento de Segredos (`.gitignore`):** O arquivo `.env` contendo as senhas reais de produção/homologação NUNCA deve ser comitado no Git.
3. **Gabarito Transparente (`.env.example`):** O repositório deve manter sempre o arquivo `.env.example` atualizado com o mapa de todas as variáveis utilizadas pelo sistema, contendo apenas valores de exemplo fictícios/placeholders.
4. **Validação na Inicialização:** O backend deve validar na inicialização (`src/config.py`) se todas as variáveis necessárias foram fornecidas.

---

## 📋 2. Mapa de Variáveis de Ambiente do Framework

| Variável | Categoria | Tipo | Obrigatório | Descrição / Exemplo Fictício |
| :--- | :--- | :---: | :---: | :--- |
| `ENV` | Servidor | String | Sim | `development` ou `production` |
| `LOG_LEVEL` | Servidor | String | Sim | `info`, `debug`, `warning`, `error` |
| `ALLOWED_ORIGINS` | Servidor | String | Sim | Domínios permitidos para CORS (ex: `*` ou `http://10.34.0.192`) |
| `APP_DB_URL` | Banco Local | String | Sim | DSN do banco SQLite local (`sqlite+aiosqlite:///data/app.db`) |
| `POSTGRES_DSN` | AGHU | String | Não | DSN PostgreSQL do AGHU (`postgresql+asyncpg://user:pass@host:5432/db`) |
| `ORACLE_DSN` | AGHU | String | Não | DSN Oracle do AGHU (`oracle+oracledb://user:pass@host:1521/service`) |
| `AD_URL` | Segurança AD | String | Não* | Servidores de AD (`ldap://servidor-ad1.ebserhnet.ebserh.gov.br:389`). *Se vazio, ativa o Mock. |
| `AD_BASEDN` | Segurança AD | String | Sim | Árvore base do AD (`DC=ebserhnet,DC=gov,DC=br`) |
| `AD_BIND_USER` | Segurança AD | String | Não | Conta de serviço para busca de grupos (`EBSERHNET\usuario_servico`) |
| `AD_BIND_PASSWORD` | Segurança AD | String | Não | Senha da conta de serviço |
| `JWT_SECRET` | Criptografia | String | Sim | Chave forte usada para assinar Tokens JWT |
| `JWT_EXP_HOURS` | Criptografia | Int | Sim | Validade do Access Token em horas (padrão: `24`) |
| `REFRESH_TOKEN_EXP_DAYS` | Criptografia | Int | Sim | Validade do Cookie HttpOnly em dias (padrão: `30`) |

---

## 🔒 3. Boas Práticas de Implantação e Deploy

### 1. Servidores Linux VM (`systemd`)
Ao implantar o serviço no Linux via `systemd`, referencie o arquivo `.env` diretamente no arquivo de unidade `/etc/systemd/system/meu-sistema.service`:
```ini
[Service]
EnvironmentFile=/caminho/para/o/projeto/.env
ExecStart=/caminho/para/o/projeto/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 2. Contêineres (`Podman` / `Docker`)
Em implantações baseadas em contêineres, passe o arquivo de ambiente através da diretiva `env_file` no `compose.yaml`:
```yaml
services:
  app:
    build: .
    env_file:
      - .env
    ports:
      - "8000:8000"
```
