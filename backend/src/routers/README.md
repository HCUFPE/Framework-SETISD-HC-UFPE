# Routers — Endpoints da API

Define os endpoints HTTP. Os routers não contêm lógica de negócio — eles recebem a requisição, validam entrada via Pydantic e delegam ao controller correspondente.

Todos os endpoints ficam sob o prefixo `/api` e são registrados em `main.py`.

---

## Endpoints por arquivo

### `auth.py` — Autenticação (`/api`)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/login` | Autentica e retorna access token. Com `remember_me=true` define cookie de refresh token. |
| POST | `/api/token/refresh` | Renova o access token usando o refresh token do cookie. |
| POST | `/api/logout` | Invalida o refresh token e limpa o cookie. |
| GET | `/api/users/me` | Retorna os dados do usuário autenticado (username, grupos, setor). |

---

### `exame.py` — Exames e Triagem (`/api/exames`)

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| POST | `/api/exames` | Recepcionista | Registra recebimento de amostra (triagem). Cria exame + frasco + retorna etiqueta. |
| GET | `/api/exames/dashboard` | Qualquer | Lista exames para o dashboard com flag de SLA. |
| GET | `/api/exames` | Qualquer | Lista todos os exames. |
| GET | `/api/exames/{id}` | Qualquer | Detalhe de um exame. |

---

### `frasco.py` — Frascos (`/api/frascos`)

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| GET | `/api/frascos/buscar` | Qualquer | Busca por `numero_solicitacao` ou `codigo_interno`. |
| GET | `/api/frascos/{id}/etiqueta` | Qualquer | Retorna payload de etiqueta para reimpressão. |
| POST | `/api/frascos/{id}/encaminhar-macroscopia` | Recepcionista | Transiciona frasco para `Aguardando Macroscopia`. |
| POST | `/api/frascos/{id}/iniciar-macroscopia` | Macroscopista | Inicia a macroscopia do frasco. |

---

### `macroscopia.py` — Macroscopia (`/api/macroscopia`)

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| GET | `/api/macroscopia/pendencias` | Macroscopista | Fila da estação: frascos aguardando ou em macroscopia. |
| POST | `/api/macroscopia` | Macroscopista | Registra descrição + gera cassetes. Transiciona frasco para `Processamento Completo`. |

---

### `processamento.py` — Processamento Técnico (`/api/processamento`)

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| GET | `/api/processamento/pendencias` | Técnico | Fila de cassetes aguardando processamento. |
| POST | `/api/processamento/lote` | Técnico | Inicia lote: agrupa cassetes e os coloca em processamento. |
| POST | `/api/processamento/lote/{id}/concluir` | Técnico | Conclui lote: gera blocos de parafina para cada cassete. |
| GET | `/api/processamento/blocos/pendencias` | Técnico | Fila de blocos aguardando corte microtômico. |
| GET | `/api/processamento/blocos/buscar` | Técnico | Busca manual por código de bloco. |
| POST | `/api/processamento/blocos/{id}/laminas` | Técnico | Gera lâminas a partir de um bloco. |
| GET | `/api/processamento/blocos/{id}/laminas` | Técnico | Lista lâminas de um bloco. |

---

### `historico.py` — Rastreabilidade (`/api/historico`)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/historico` | Lista o histórico de movimentação. Filtra por `id_exame`, `id_frasco` ou `id_cassete` (ao menos um obrigatório). |

---

### `paciente.py` — Consulta de Pacientes (`/api/pacientes`)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/pacientes` | Lista pacientes (fonte: CSV ou AGHU conforme configuração). |
| GET | `/api/pacientes/{codigo}` | Busca paciente por código. |

---

### Routers auxiliares (placeholders)

| Arquivo | Prefixo | Status |
|---|---|---|
| `admin.py` | `/api` | Rota de verificação de perfil admin |
| `aih.py` | `/api/aih` | Placeholder — integração AGHU futura |
| `bpa.py` | `/api/bpa` | Placeholder — integração AGHU futura |
| `material.py` | `/api/material` | Placeholder — integração AGHU futura |

---

## Padrão de proteção de rotas

```python
current_user: dict = Depends(require_perfil(Perfil.RECEPCIONISTA))
```

Rotas sem perfil específico ainda exigem autenticação via `require_perfil()` (sem argumentos), que em modo permissivo aceita qualquer usuário autenticado.

A documentação interativa completa dos endpoints (com exemplos de request/response) está disponível em `/docs` quando o servidor está rodando.
