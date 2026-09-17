# Padrão de Auditoria e Trilha de Mudanças (Audit Trail & Logging)
> **Norma Técnica de Registro de Auditoria, Conformidade LGPD e Rastreabilidade**  
> *Hospital das Clínicas da UFPE (HC-UFPE / EBSERH)*

---

## 🏛️ 1. Objetivo e Princípios

Para atender aos requisitos de **segurança da informação, governança corporativa e conformidade com a LGPD**, todas as aplicações desenvolvidas no HC-UFPE devem contar com um mecanismo padronizado de **Trilha de Auditoria (Audit Trail)**.

### Princípios da Auditoria:
1. **Identificação Completa:** Todo evento auditado deve identificar o **Usuário**, **Data/Hora (UTC)**, **Ação**, **Recurso Afetado** e **IP de Origem**.
2. **Rastreabilidade de Mudanças (Before / After):** Alterações de dados sensíveis devem capturar o **estado anterior (`dados_anteriores`)** e o **novo estado (`dados_novos`)** em formato JSON estruturado.

---

## 🏷️ 2. Entendendo as 3 Categorias de Auditoria

Para facilitar buscas e relatórios de auditoria da TI e da Gestão Hospitalar, todos os registros são obrigatoriamente classificados em 3 categorias:

1. **`SEGURANCA` (Gestão de Acesso, Contas e Perfis):**
   * **O que auditamos:** Ações realizadas por usuários com perfil `ADMINISTRADOR` que alteram os direitos de acesso ao sistema.
   * **Exemplo:** Alterar o perfil de um usuário de `ENFERMAGEM` para `MEDICO`, cadastrar novos colaboradores, bloquear contas.

2. **`NEGOCIO_CLINICO` (Operação do Hospital e Pacientes):**
   * **O que auditamos:** Ações rotineiras realizadas por profissionais de saúde (`MEDICO`, `ENFERMAGEM`, `FARMACEUTICO`) na assistência ao paciente.
   * **Exemplo:** Conceder alta a um paciente na UTI, alterar o estado de um leito para `MANUTENCAO`, registrar sinais vitais ou dispensar medicamentos.

3. **`CONFIGURACAO` (Parâmetros Globais do Sistema):**
   * **O que auditamos:** Alterações nos parâmetros técnicos de funcionamento do sistema.
   * **Exemplo:** Alterar o tempo limite de aviso de leito vagar ou regras globais de notificação.

---

## 📋 3. Estrutura da Tabela `audit_logs`

A tabela de auditoria é mantida no banco local da aplicação (`data/app.db`) e possui o seguinte esquema:

| Campo | Tipo | Nulo | Descrição / Exemplo |
| :--- | :--- | :---: | :--- |
| `id` | Integer | Não | Chave primária autoincrementável |
| `created_at` | DateTime (UTC) | Não | Data e hora exata da ocorrência |
| `usuario` | String | Não | Login do usuário executor (ex: `admin`, `joao.silva`) |
| `categoria` | String | Não | Categoria do evento: `SEGURANCA`, `NEGOCIO_CLINICO`, `CONFIGURACAO` |
| `acao` | String | Não | Nome da ação executada (ex: `ALTERAR_PERFIL_USUARIO`, `REGISTRAR_ALTA`) |
| `recurso` | String | Não | Identificador do recurso alterado (ex: `usuario:joao.silva`, `paciente:12345`) |
| `dados_anteriores` | Text (JSON) | Sim | Estado dos dados ANTES da alteração (`before`) |
| `dados_novos` | Text (JSON) | Sim | Estado dos dados DEPOIS da alteração (`after`) |
| `ip_origem` | String | Sim | IP de origem da requisição HTTP (ex: `10.34.0.50`) |

---

## 💻 4. Exemplos Práticos de Uso no Backend

```python
from src.helpers.audit_helper import registrar_auditoria

# Exemplo 1: Perfis ADMINISTRADOR alterando perfil de usuário (Categoria SEGURANCA)
await registrar_auditoria(
    db=session,
    usuario=current_user["username"],
    categoria="SEGURANCA",
    acao="ALTERAR_PERFIL_USUARIO",
    recurso=f"usuario:{usuario_alvo.username}",
    dados_anteriores={"perfil": "ENFERMAGEM"},
    dados_novos={"perfil": "MEDICO"},
    ip_origem=request.client.host
)

# Exemplo 2: Perfil MEDICO registrando alta hospitalar (Categoria NEGOCIO_CLINICO)
await registrar_auditoria(
    db=session,
    usuario=current_user["username"],
    categoria="NEGOCIO_CLINICO",
    acao="REGISTRAR_ALTA_MEDICA",
    recurso=f"paciente:{paciente_id}",
    dados_anteriores={"status": "EM_UTI"},
    dados_novos={"status": "ALTA_MEDICA"},
    ip_origem=request.client.host
)
```
