# Modelo de Dados e Dicionário — SAE-HC

## 1. Modelo Entidade-Relacionamento

```mermaid
erDiagram
  FORMS_RESPONSE ||--o| SOLICITACAO : gera
  SOLICITACAO ||--o{ SOLICITACAO_ITEM_EXAME : contem
  SOLICITACAO ||--o{ DIVERGENCIA : possui
  SOLICITACAO ||--o{ ALERTA : gera
  SOLICITACAO ||--o{ CONTATO_PACIENTE : registra
  SOLICITACAO ||--o{ AGENDAMENTO : resulta
  SOLICITACAO ||--o{ AUDIT_LOG : rastreia
  CRITERIO_PRIORIZACAO }o--|| VERSAO_CRITERIOS : pertence
  USUARIO_PERFIL ||--o{ AUDIT_LOG : autoria

  FORMS_RESPONSE {
    int id PK
    string response_id UK
    string form_id
    text payload_cripto
    string status
    int tentativas
    text ultimo_erro
    string ip_origem
    datetime recebido_em
    datetime processado_em
    string solicitacao_id
    datetime deleted_at
  }
  WEBHOOK_NONCE {
    int id PK
    string nonce UK
    datetime criado_em
    datetime expira_em
  }
  SOLICITACAO {
    uuid id PK
    string protocolo
    string forms_response_id
    string codigo_solicitacao_aghux
    string prontuario
    string paciente_nome
    string cpf_cripto
    string cns_cripto
    string cpf_hash
    string cns_hash
    string paciente_chave
    string exame
    text itens_exame
    string prioridade
    string status
    int pontuacao
    datetime recebida_em
    datetime criado_em
    datetime atualizado_em
    datetime deleted_at
  }
  SOLICITACAO_ITEM_EXAME {
    int id PK
    uuid solicitacao_id FK
    string codigo_exame
    string nome_exame
    datetime deleted_at
  }
  CRITERIO_PRIORIZACAO {
    uuid id PK
    uuid versao_id FK
    string nome
    string descricao
    int peso
    int ordem
    bool ativo
  }
  VERSAO_CRITERIOS {
    uuid id PK
    int numero
    string justificativa
    string autor
    datetime criado_em
  }
  DIVERGENCIA {
    uuid id PK
    uuid solicitacao_id FK
    string campo
    string valor_formulario
    string valor_aghux
    bool tratada
    text justificativa
    datetime criado_em
    datetime deleted_at
  }
  ALERTA {
    uuid id PK
    uuid solicitacao_id FK
    string campo
    string mensagem
    string severidade
    datetime criado_em
    datetime deleted_at
  }
  CONTATO_PACIENTE {
    uuid id PK
    uuid solicitacao_id FK
    string canal
    string resultado
    string operador
    datetime realizado_em
  }
  AGENDAMENTO {
    uuid id PK
    uuid solicitacao_id FK
    uuid slot_id FK
    string paciente_chave
    string status
    string autor
    datetime criado_em
  }
  USUARIO_PERFIL {
    uuid id PK
    string login_ad
    string nome
    string email
    string lotacao
    string perfil
    bool ativo
    datetime deleted_at
  }
  AUDIT_LOG {
    int id PK
    datetime created_at
    string usuario
    string categoria
    string acao
    string recurso
    json dados_anteriores
    json dados_novos
    string ip_origem
  }
```

### Agenda local, endereço e distância (v0.6.0)

```mermaid
erDiagram
  AGENDA_SLOTS ||--o{ AGENDAMENTO : preenche
  SOLICITACAO ||--o{ AGENDAMENTO : resulta
  SOLICITACAO ||--o{ PACIENTE_ENDERECO : "mesma chave derivada"

  AGENDA_SLOTS {
    uuid id PK
    string unidade
    string codigo_exame
    string nome_exame
    datetime inicio
    datetime fim
    int capacidade
    string situacao
    datetime deleted_at
  }
  AGENDAMENTO {
    uuid id PK
    uuid solicitacao_id FK
    uuid slot_id FK
    string paciente_chave
    string status
    string autor
    text justificativa
    datetime criado_em
    datetime cancelado_em
    datetime deleted_at
  }
  PACIENTE_ENDERECO {
    uuid id PK
    string paciente_chave
    text cep_cripto
    text logradouro_cripto
    text numero_cripto
    text complemento_cripto
    text bairro_cripto
    string cidade
    string estado
    float latitude
    float longitude
    float distancia_km
    string distancia_fonte
    datetime calculado_em
    datetime deleted_at
  }
```

`paciente_chave` é um HMAC-SHA256 de 64 caracteres derivado do prontuário normalizado (com fallback para CPF/CNS normalizados), calculado com chave derivada de `PHI_ENCRYPTION_KEY`. Ela agrupa solicitações, agendamentos e endereço do mesmo paciente sem expor PHI. Agendamentos `ATIVO` e propostas `PROPOSTO` ocupam a vaga: a unicidade por `(slot_id, paciente_chave)` e a capacidade são validadas no controller, pois índice parcial não é portátil no SQLite.

## 2. Dicionário de Dados

| Entidade | Finalidade | Regras principais |
| :--- | :--- | :--- |
| `FORMS_RESPONSE` | Evento idempotente do webhook do Microsoft Forms via Power Automate. | `response_id` único; payload bruto criptografado em `payload_cripto`; status `PENDENTE`, `PROCESSADA`, `DUPLICADA` ou `ERRO`; `tentativas`, `ultimo_erro`, `ip_origem`, `recebido_em`, `processado_em` e `solicitacao_id`; `deleted_at` para exclusão lógica. |
| `WEBHOOK_NONCE` | Nonce já consumido pelo webhook. | `nonce` único, com `criado_em` e `expira_em`; impede replay mesmo quando a assinatura HMAC é válida. Não tem `deleted_at` (controle de segurança). |
| `SOLICITACAO` | Uma requisição de exame recebida do formulário externo. | `id` UUID, `protocolo` no formato `FORMS-<responseId>` e `forms_response_id` único; CPF/CNS criptografados com AES-GCM e hashes HMAC para deduplicação; `paciente_chave` HMAC de 64 hex agrupa solicitações e agendamentos do mesmo paciente; `deleted_at` para exclusão lógica; status controlado por máquina de estados em `05-interfaces.md`. No mock atual, a identificação de origem é `codigoSolicitacaoAghux` + `prontuario`, pois o export não contém CPF/CNS. |
| `SOLICITACAO_ITEM_EXAME` | Um exame por linha da solicitação. | FK para `solicitacoes.id`; código e nome do exame; `deleted_at` para exclusão lógica (reprocessamento desativa os itens anteriores). |
| `DIVERGENCIA` | Diferença entre formulário e cadastro AGHUX. | FK para `solicitacoes.id`; `tratada`, `justificativa`, `criado_em` e `deleted_at`. Não pode ser ignorada; exige correção ou justificativa antes da validação (RN-04). |
| `ALERTA` | Inconsistência detectada no recebimento (RF004). | FK para `solicitacoes.id`; `campo`, `mensagem`, `severidade`, `criado_em` e `deleted_at`. Orienta notificação ao paciente (RF019). |
| `CONTATO_PACIENTE` | Registro de aceite, recusa ou sem resposta. | FK para `solicitacoes.id`; `canal`, `resultado` (`ACEITE`, `RECUSA`, `SEM_RESPOSTA`), `observacao`, `operador`, `realizado_em` e `deleted_at`. Pode ser registrado enquanto a solicitação está em `AGUARDANDO_CONTATO`, `AGUARDANDO_CONFIRMACAO` ou `AGUARDANDO_REAGENDAMENTO`; aceite é pré-condição da reserva (RN-07). |
| `AGENDA_SLOTS` | Vaga local cadastrada pela Chefia da Central, Área Gestora ou ADMIN_TI. | Unidade, exame (código/nome), `inicio`/`fim`, `capacidade`, `situacao` (`DISPONIVEL`, `LOTADO`, `ENCERRADO`), `criado_em`, `atualizado_em` e `deleted_at`. `ocupadas` é derivada dos agendamentos `ATIVO` e das propostas `PROPOSTO`, nunca armazenada, e inclui outros pacientes. |
| `AGENDAMENTO` | Reserva na agenda local do SAE-HC, com confirmação operacional do operador. | FK para `solicitacoes.id` e `agenda_slots.id`; `paciente_chave`, `status` (`PROPOSTO`, `ATIVO`, `CANCELADO`, `CONCLUIDO`), `autor`, `justificativa`, `criado_em`, `cancelado_em` e `deleted_at`. `PROPOSTO` reserva vaga e só vira `ATIVO` após confirmação do operador. Toda reserva exige aceite e divergências tratadas; bloqueia choque do mesmo paciente (RN-05) e não ultrapassa a capacidade (RN-09). Remarcação e cancelamento exigem justificativa e devolvem a vaga na mesma transação. |
| `PACIENTE_ENDERECO` | Endereço informado no Forms e última distância calculada até o hospital. | `paciente_chave`; CEP, logradouro, número, complemento e bairro cifrados com AES-GCM; cidade/UF em claro; `latitude`, `longitude`, `distancia_km`, `distancia_fonte` (`OSM`, `MOCK`, `INDISPONIVEL`), `calculado_em` e `deleted_at`. Sem endereço no payload, nenhum registro é criado e nenhuma distância é inventada. |
| `CRITERIO_PRIORIZACAO` | Regra que compõe a pontuação da fila. | Peso inteiro, ordem e situação ativa/inativa. |
| `VERSAO_CRITERIOS` | Conjunto versionado de critérios. | Toda alteração cria nova versão com justificativa; versões anteriores não são apagadas. |
| `USUARIO_PERFIL` | Autorização local complementar ao AD. | Login corporativo ativo + perfil ativo; soft delete; perfis em `05-interfaces.md`. |
| `AUDIT_LOG` | Trilha imutável de mutações. | Somente inserção; antes/depois em JSON; categorias `SEGURANCA`, `NEGOCIO_CLINICO`, `CONFIGURACAO`. |

As tabelas físicas da integração são `forms_responses`, `webhook_nonces`, `solicitacoes`, `solicitacao_itens_exame`, `divergencias` e `alertas`, criadas pela migração Alembic **`c4f1a7d9e2b3`** (revises `8a2efbe37bb6`). A v0.3.0 acrescentou a migração **`e7c1a9d4b3f2`** (revises `c4f1a7d9e2b3`): cria `agenda_slots`, `agendamentos`, `contatos_paciente` e `paciente_enderecos` e adiciona `solicitacoes.paciente_chave`. A v0.4.0 **não altera o esquema físico**; apenas amplia os valores possíveis de `agendamentos.status` (`PROPOSTO`) e de `solicitacoes.status`, ambos armazenados como texto. A v0.5.0 também **não altera o esquema físico**: a fila de propostas é um DTO de leitura montado a partir de `agendamentos`, `solicitacoes` e `solicitacao_itens_exame`. A v0.6.0 **também não altera o esquema**: remoção usa o `deleted_at` existente em `agenda_slots` e a cópia semanal apenas insere novas linhas com o mesmo contrato de `AgendaSlot`. Tabelas do framework mantidas: `REFRESH_TOKENS`, `AUDIT_LOGS` (esta última, somente inserção). Bancos novos são criados por `create_all`; a migração `e7c1a9d4b3f2` deve ser aplicada via Alembic em bancos já existentes no deploy.

### [SCHEMA] Esquema JSON — FormsEvento (resumo sem PHI)

Contrato devolvido pelos endpoints administrativos e consumido pela tela `/integracoes`; não contém payload, CPF nem CNS.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FormsEvento",
  "type": "object",
  "properties": {
    "responseId": { "type": "string" },
    "formId": { "type": "string" },
    "status": { "type": "string", "enum": ["PENDENTE", "PROCESSADA", "DUPLICADA", "ERRO"] },
    "tentativas": { "type": "integer", "minimum": 0 },
    "ultimoErro": { "type": ["string", "null"] },
    "recebidoEm": { "type": "string", "format": "date-time" },
    "processadoEm": { "type": ["string", "null"], "format": "date-time" },
    "solicitacaoId": { "type": ["string", "null"], "format": "uuid" },
    "divergencias": { "type": "integer", "minimum": 0 },
    "alertas": { "type": "integer", "minimum": 0 }
  },
  "required": ["responseId", "formId", "status", "tentativas", "recebidoEm", "divergencias", "alertas"]
}
```

### [SCHEMA] Esquema JSON — Solicitacao (resumo para a API)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Solicitacao",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "protocolo": { "type": "string" },
    "pacienteNome": { "type": "string" },
    "codigoSolicitacaoAghux": { "type": "string" },
    "prontuario": { "type": "string" },
    "telefone": { "type": "string" },
    "cidade": { "type": "string" },
    "estado": { "type": "string" },
    "exame": { "type": "string", "description": "Primeiro exame do grupo; ver itensExame" },
    "itensExame": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "codigoExame": { "type": "string" },
          "nomeExame": { "type": "string" }
        },
        "required": ["codigoExame", "nomeExame"]
      }
    },
    "unidadeSolicitante": { "type": "string" },
    "solicitanteNome": { "type": "string" },
    "status": {
      "type": "string",
      "enum": ["RECEBIDA", "PENDENTE_CORRECAO", "AGUARDANDO_CONTATO", "AGUARDANDO_CONFIRMACAO", "AGUARDANDO_REAGENDAMENTO", "AGENDADA", "CANCELADA"]
    },
    "pontuacao": { "type": "integer", "minimum": 0 },
    "prioridade": { "type": "string", "enum": ["ALTA", "MEDIA", "BAIXA"] },
    "recebidaEm": { "type": "string", "format": "date-time" }
  },
  "required": ["id", "protocolo", "pacienteNome", "exame", "status", "pontuacao", "prioridade", "recebidaEm"]
}
```

### [SCHEMA] Esquema JSON — AgendaSlot, Agendamento e PropostaAgendamentoFila (v0.6.0)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgendaSlot",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "unidade": { "type": "string" },
    "codigoExame": { "type": "string" },
    "nomeExame": { "type": "string" },
    "inicio": { "type": "string", "format": "date-time" },
    "fim": { "type": "string", "format": "date-time" },
    "capacidade": { "type": "integer", "minimum": 1 },
    "ocupadas": { "type": "integer", "minimum": 0, "description": "Agendamentos ATIVOS e propostas PROPOSTO, inclusive de outros pacientes" },
    "livres": { "type": "integer", "minimum": 0 },
    "status": { "type": "string", "enum": ["DISPONIVEL", "LOTADO", "ENCERRADO"] }
  },
  "required": ["id", "unidade", "inicio", "fim", "capacidade", "ocupadas", "livres", "status"]
}
```

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agendamento",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "solicitacaoId": { "type": "string", "format": "uuid" },
    "protocolo": { "type": "string" },
    "pacienteChave": { "type": "string", "description": "HMAC sem PHI" },
    "pacienteNome": { "type": "string" },
    "prontuario": { "type": "string" },
    "unidade": { "type": "string" },
    "exame": { "type": "string" },
    "slotId": { "type": "string", "format": "uuid" },
    "dataHora": { "type": "string", "format": "date-time" },
    "status": { "type": "string", "enum": ["PROPOSTO", "ATIVO", "CANCELADO", "CONCLUIDO"] },
    "confirmadoPor": { "type": "string" },
    "criadoEm": { "type": "string", "format": "date-time" },
    "justificativa": { "type": ["string", "null"] }
  },
  "required": ["id", "solicitacaoId", "pacienteChave", "slotId", "dataHora", "status", "criadoEm"]
}
```

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PropostaAgendamentoFila",
  "type": "object",
  "properties": {
    "agendamentoId": { "type": "string", "format": "uuid" },
    "solicitacaoId": { "type": "string", "format": "uuid" },
    "protocolo": { "type": "string" },
    "pacienteNome": { "type": "string" },
    "prontuario": { "type": "string" },
    "prioridade": { "type": "string", "enum": ["ALTA", "MEDIA", "BAIXA"] },
    "pontuacao": { "type": "integer", "minimum": 0, "maximum": 100 },
    "unidadeSolicitante": { "type": "string" },
    "exames": { "type": "string" },
    "status": { "type": "string", "enum": ["PROPOSTO"] },
    "statusSolicitacao": { "type": "string" },
    "dataHora": { "type": "string", "format": "date-time" },
    "unidade": { "type": "string" },
    "nomeExame": { "type": "string" },
    "recebidaEm": { "type": "string", "format": "date-time" },
    "tempoNaFilaHoras": { "type": "integer", "minimum": 0 }
  },
  "required": ["agendamentoId", "solicitacaoId", "prioridade", "pontuacao", "status", "tempoNaFilaHoras"]
}
```

`SugestaoAgendamento` combina um `AgendaSlot`, `pontuacao` (`0..100`), `motivos` (texto legível), `distanciaKm` (`number|null`) e `distanciaOrigem` (`OSM`, `MOCK` ou `INDISPONIVEL`). O endereço do paciente nunca faz parte deste contrato.

A simulação da agenda devolve `{ geradas, solicitacoes, dias, propostas }`: contadores operacionais e as linhas `PropostaAgendamentoFila` já ordenadas, sem dados de endereço. Cada proposta gerada segue o mesmo contrato `Agendamento` com `status: "PROPOSTO"`; a confirmação do operador devolve o contrato com `status: "ATIVO"`, e a não confirmação devolve `status: "CANCELADO"` com justificativa. Nenhum desses contratos carrega `dados_anteriores`, endereço, CPF ou CNS.

### [SCHEMA] Esquema JSON — CriterioPriorizacao

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CriterioPriorizacao",
  "type": "object",
  "properties": {
    "id": { "type": "string" },
    "chave": { "type": "string", "description": "Chave do atributo da solicitação usada no cálculo da pontuação" },
    "nome": { "type": "string", "minLength": 3 },
    "descricao": { "type": "string" },
    "peso": { "type": "integer", "minimum": 0, "maximum": 100 },
    "ordem": { "type": "integer", "minimum": 1 },
    "ativo": { "type": "boolean" }
  },
  "required": ["id", "nome", "peso", "ordem", "ativo"]
}
```

### [SCHEMA] Esquema JSON — AuditLog

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AuditLog",
  "type": "object",
  "properties": {
    "usuario": { "type": "string" },
    "categoria": { "type": "string", "enum": ["SEGURANCA", "NEGOCIO_CLINICO", "CONFIGURACAO"] },
    "acao": { "type": "string" },
    "recurso": { "type": "string" },
    "dados_anteriores": { "type": ["object", "null"] },
    "dados_novos": { "type": ["object", "null"] },
    "ip_origem": { "type": ["string", "null"] }
  },
  "required": ["usuario", "categoria", "acao", "recurso"]
}
```

### [MAPEAMENTO] Export CSV do AGHUX → Solicitacao (mocks)

O fixture `frontend/src/mocks/dadosAghux.json` é gerado por `scripts/importar_dados_aghux.py` a partir do export `Documentos de Apoio/_SELECT_Dados_do_Paciente_*.csv`. Cada linha é um item de exame; linhas com o mesmo `codigo_solicitacao` são agrupadas em uma única solicitação com `itensExame[]`.

| Coluna do export | Campo da solicitação | Observação |
| :--- | :--- | :--- |
| `codigo_solicitacao` | `codigoSolicitacaoAghux`, `protocolo` | Chave de agrupamento. |
| `pac_prontuario` | `prontuario` | Identificador do paciente no AGHU. |
| `pac_nome` | `pacienteNome` | Nome já anonimizado no export. |
| `telefone` | `telefone` | Fixo `81999999999` no export; não é telefone real. |
| `cidade`, `estado` | `cidade`, `estado` | UF por extenso no export. |
| `data_solicitao` | `recebidaEm` | Data real preservada; o maior valor do export é 28/09/2026, estendido para 25/11/2026 pelas solicitações simuladas no fixture. |
| `unidade_solicitante` | `setorSolicitante`, `tipoExame` | `tipoExame` é categoria derivada para filtros. |
| `codigo_exame`, `nome_exame` | `itensExame[]` | Exames de uma mesma solicitação. |
| `id_funcionario`, `nome_funcionario` | `solicitanteCodigo`, `solicitanteNome` | Solicitante no AGHU. |

`urgenciaClinica` e `idade` não existem no export e são valores neutros simulados, sinalizados em `atributosSimulados`. `tempoEspera` e `complexidadeExame` são derivados de campos reais. O "agora" da simulação é a referência do fixture (`2026-11-25T16:05:34.227`); a referência original do export (`2026-09-28T16:05:34.227`) permanece apenas como proveniência dos registros reais.

### [MAPEAMENTO] Resposta do Forms → Solicitacao (atualizado na v0.3.0)

O corpo `resposta` enviado pelo Power Automate é normalizado pelo mapa de apelidos `FORMS_FIELD_MAP` (`src/config.py`): `nome`, `prontuario`, `codigoSolicitacaoAghux`, `cpf`, `cns`, `telefone`, `cep`, `logradouro`, `numero`, `complemento`, `bairro`, `cidade`, `estado`, `codigoExame`, `nomeExame`, `unidadeSolicitante` e `submittedAt`. O provedor `MockFormsProvider` completa campos ausentes; `PowerAutomateFormsProvider` nunca inventa valores.

| Origem | Destino | Regra |
| :--- | :--- | :--- |
| `responseId` do webhook | `forms_responses.response_id`, `solicitacoes.forms_response_id`, `protocolo` | Chave de idempotência; protocolo `FORMS-<responseId>`. |
| `resposta` (JSON bruto) | `forms_responses.payload_cripto` | AES-GCM; decifrado apenas no processamento assíncrono. |
| `submittedAt` | `solicitacoes.recebida_em` | Ausente → `recebido_em` do evento. |
| `prontuario` / `codigoSolicitacaoAghux` | Cruzamento com o AGHUX | `AghuxJsonProvider` indexa prontuário e código da solicitação da fixture versionada. |
| `cpf` / `cns` | `cpf_cripto`, `cns_cripto`, `cpf_hash`, `cns_hash` | Cifrotexto para guarda; HMAC para deduplicação; ausentes ficam nulos. |
| Exames do cadastro ou do formulário | `itens_exame` e `solicitacao_itens_exame` | Um exame por linha, com código e nome. |
| Nome, telefone, cidade/UF, unidade e exames | `divergencias`, `alertas` | Comparação normalizada com o AGHUX; sem correspondência gera alerta de severidade `ALTA`. |
| `cep`, `logradouro`, `numero`, `complemento`, `bairro` | `paciente_enderecos.*_cripto` | Só quando presentes no payload; AES-GCM com a mesma chave de PHI. Cidade/UF são mantidas em claro. |
| Endereço + coordenadas do hospital | `paciente_enderecos.latitude`, `longitude`, `distancia_km`, `distancia_fonte`, `calculado_em` | Nominatim geocodifica e OSRM calcula a rota; cache por hash do endereço, timeout e `User-Agent`. Falha → `distanciaKm` nulo e origem `INDISPONIVEL`. |

A pontuação segue a mesma regra dos mocks: urgência clínica e idade neutras valem `5` até a integração com a triagem/prontuário; tempo de espera derivado de `recebida_em` (`min(10, round(horas/144))`); complexidade estimada pela sigla do exame. Pesos `40/25/20/15`, pontuação `round(soma/10)` limitada a `0..100`, com `ALTA >= 70`, `MEDIA >= 40` e `BAIXA` abaixo disso. O reprocessamento reativa o cálculo sem criar outro evento e desativa (`deleted_at`) itens, divergências e alertas anteriores.

## 3. Regras de Integridade
- CPF/CNS armazenados com AES-GCM (`cryptography`, nonce de 96 bits, chave de 32 bytes); listagens exibem somente máscara `***` nos últimos 4 dígitos. O export usado nos mocks não contém CPF/CNS e o formulário sem esses campos não inventa valores.
- Hashes HMAC-SHA256 (`cpf_hash`, `cns_hash`) existem apenas para busca/deduplicação; payload, auditoria, logs e respostas da API nunca trazem CPF/CNS em claro.
- `forms_responses.response_id`, `webhook_nonces.nonce` e `solicitacoes.forms_response_id` são únicos; nonce repetido é rejeitado antes da idempotência da resposta.
- Proibida exclusão física: todas as entidades editáveis usam `deleted_at`; `AUDIT_LOG` é somente de inserção (`WEBHOOK_NONCE` é controle de segurança e não é editável).
- Somente a Área Gestora cria versões de critérios, e toda versão exige justificativa (RN-03).
- Nenhuma solicitação pode ser agendada sem aceite de contato registrado e divergências tratadas (RN-04/RN-07); o agendamento real no AGHU permanece fora desta entrega.
- Trilha de auditoria obrigatória em `audit_logs` para todas as mutações, inclusive a importação e falhas de processamento do webhook (`webhook:microsoft-forms`, categoria `NEGOCIO_CLINICO`), agendamentos/remarcações/cancelamentos (`NEGOCIO_CLINICO`) e criação/edição de vagas (`CONFIGURACAO`).
- `paciente_chave` é derivada por HMAC e nunca substitui PHI em claro; nenhuma API, log ou auditoria devolve CPF/CNS, endereço completo ou coordenadas do paciente.
- Agendamento `ATIVO` não pode exceder `agenda_slots.capacidade` nem duplicar `(slot_id, paciente_chave)`; a ocupação considera todos os agendamentos ativos, mesmo quando a resposta de calendário está filtrada por paciente.
- `distancia_km` é nula quando o endereço não foi informado ou quando o provedor falha; `distancia_fonte` registra `OSM`, `MOCK` (somente testes) ou `INDISPONIVEL`. Nunca se inventa coordenada ou quilometragem.
- Remarcação e cancelamento são mutações com `justificativa` obrigatória e devolução da vaga anterior na mesma transação da auditoria.
