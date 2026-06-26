# Schemas — Contratos de Entrada e Saída

Modelos Pydantic que definem o formato dos dados nas requisições e respostas da API. Separados dos modelos ORM (`models/`) para que a API possa evoluir independentemente do schema do banco.

---

## Convenção de nomenclatura

| Sufixo | Uso |
|---|---|
| `Create` / `Request` | Dados de entrada (corpo da requisição) |
| `Out` | Dados de saída (resposta da API) |
| `Detalhe` | Saída enriquecida com dados de entidades relacionadas (resultado de JOIN) |
| `Result` | Resposta composta que agrega múltiplas entidades de uma operação |

---

## Arquivo por arquivo

### `exame.py`

- **`ExameCreate`** — input da triagem: dados do paciente, tipo de exame, tipo de peça, topografia e número do AGHU (opcional)
- **`ExameOut`** — saída padrão com os campos do modelo ORM
- **`DashboardExameOut`** — saída específica para o dashboard: inclui nome do paciente (via join) e flag `atrasado` (calculada pelo backend, SLA ≥ 20 dias)

### `frasco.py`

- **`FrascoOut`** — campos do modelo ORM
- **`FrascoDetalhe`** — enriquecido com dados do exame e paciente; usado nas filas de macroscopia e na busca manual

### `cassete.py`

- **`CasseteOut`** — campos do modelo ORM
- **`CasseteFilaOut`** — enriquecido com dados do frasco, exame e paciente; usado na fila de processamento

### `macroscopia.py`

- **`MacroscopiaCreate`** — input: `id_frasco`, `descricao`, `numero_cassetes`
- **`MacroscopiaOut`** — campos do modelo ORM

### `bloco.py`

- **`BlocoOut`** — campos do modelo ORM
- **`BlocoDetalhe`** — enriquecido com cassete, exame e paciente
- **`GerarLaminasRequest`** — input da geração de lâminas: `quantidade` (1–20) e `coloracao` (padrão `"HE"`)

### `lamina.py`

- **`LaminaOut`** — campos do modelo ORM incluindo `codigo_lamina` e `coloracao`
- **`GerarLaminasResult`** — resposta da geração: bloco + lista de lâminas + etiquetas

### `processamento.py`

- **`IniciarLoteRequest`** — input: lista de `cassete_ids`, `responsavel`, `observacoes`
- **`ConcluirLoteRequest`** — input: `observacoes`
- **`LoteOut`** — campos do modelo ORM

### `paciente.py`

- **`PacienteInput`** — input da triagem: `nome`, `cpf`, `cns`, `data_nascimento`, `origem`
- **`PacienteOut`** — saída do modelo ORM

### `historico.py`

- **`HistoricoOut`** — todos os campos do histórico de movimentação: etapa, status anterior/novo, usuário, IP, timestamp

### `etiqueta.py`

- **`EtiquetaOut`** — payload para impressão: `tipo`, `numero_solicitacao`, `codigo` (código interno ou de bloco/lâmina) e `qr_code` (string). Devolvido em toda operação que gera uma nova entidade física.

### `resultados.py`

Schemas de resposta para operações compostas (que criam múltiplas entidades de uma vez):

- **`TriagemResult`** — resposta do registro de recebimento: exame + frasco + etiqueta
- **`MacroscopiaResult`** — resposta do registro de macroscopia: registro + frasco + lista de cassetes + etiquetas

---

## Por que separar schemas de models?

O modelo ORM (`models/exame.py`) reflete exatamente a tabela no banco — incluindo chaves estrangeiras, campos de auditoria e detalhes internos. O schema de saída (`ExameOut`) expõe apenas o que faz sentido para quem consome a API. Isso permite:

- Renomear campos na API sem alterar o banco (ex: `data_recebimento` → `data_entrada` no dashboard)
- Incluir dados calculados que não existem no banco (ex: `atrasado`, `tempoNaEtapa`)
- Evitar expor dados sensíveis ou internos inadvertidamente
