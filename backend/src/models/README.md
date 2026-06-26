# Models — Modelos de Dados (ORM)

Definição das tabelas do banco de dados da aplicação usando SQLAlchemy. Todos os modelos herdam de `Base` (declarado em `resources/database.py`), o que os registra automaticamente no metadata do SQLAlchemy para criação de tabelas e geração de migrations.

O banco de dados da aplicação é **SQLite em desenvolvimento** e **PostgreSQL em produção** — o mesmo código ORM funciona nos dois sem alterações.

> Os dados do AGHU (pacientes HC, AIHs, etc.) ficam em banco separado (PostgreSQL externo, somente leitura) e são acessados por SQL direto nos providers, não por esses modelos.

---

## Hierarquia de entidades

```
PacienteLocal
└── Exame  (1 paciente : N exames)
    └── Frasco  (1 exame : 1 frasco nesta fase)
        └── Macroscopia  (registro da descrição)
        └── Cassete  (N cassetes por frasco, gerados na macroscopia)
            └── LoteProcessamento  (N cassetes por lote)
            └── BlocoParafina  (1 bloco por cassete)
                └── Lamina  (N lâminas por bloco)

HistoricoMovimentacao  (log append-only, referencia exame, frasco ou cassete)
RefreshToken  (tokens de sessão dos usuários)
```

---

## Modelos

### `PacienteLocal`

Cache local de pacientes. Pacientes do HC são importados do AGHU na triagem; pacientes SUS são cadastrados diretamente aqui.

- Identificação: `cpf` (11 dígitos) ou `cns` (15 dígitos) — ao menos um obrigatório
- Campo `origem`: `"SUS"` ou `"HC"`
- Soft delete via campo `ativo`

---

### `Exame`

Representa o pedido de exame anatomopatológico.

- `numero_solicitacao`: identificador público no formato `HP-0001/26.1` (único no banco)
- `sequencial`, `ano`, `semestre`: partes do número, armazenados separados para facilitar o cálculo do próximo sequencial
- `tipo_exame`: HP, IHQ, HPDerm, CCV, CG, RevInt ou Congela
- `numero_exame_aghu`: referência ao sistema legado (opcional)
- `status`: gerenciado exclusivamente pela máquina de estados em `services/maquina_estados.py`

---

### `Frasco`

Recipiente físico recebido na triagem. Nesta fase cada exame tem um frasco.

- `codigo_interno`: identificador legível (`HP-0001/26.1-F1`)
- `qr_code`: string no formato padrão, gerada na triagem e usada para impressão futura
- `descricao_macroscopia` e `numero_cassetes_gerados`: preenchidos na etapa de macroscopia

---

### `Cassete`

Fragmento de tecido incluído em parafina durante o processamento. Gerado na macroscopia.

- `letra_fragmento`: A, B, C... (única por frasco)
- Chave única composta: `(id_frasco, letra_fragmento)`
- `id_lote_processamento`: preenchido quando o cassete entra em um lote (nullable antes disso)

---

### `BlocoParafina`

Bloco de parafina gerado ao concluir o processamento de um cassete.

- `codigo_bloco`: `HP-0001/26.1-A` (número de solicitação + letra do cassete)
- Relação 1:1 com Cassete

---

### `Lamina`

Lâmina de vidro gerada a partir do corte microtômico de um bloco.

- `codigo_lamina`: `HP-0001/26.1-A-L1` (código do bloco + número sequencial)
- `numero_lamina`: sequencial dentro do bloco (não reinicia entre diferentes blocos do mesmo exame)
- `coloracao`: "HE" por padrão; pode ser Giemsa, PAS, etc.
- Chave única composta: `(id_bloco, numero_lamina)`

---

### `LoteProcessamento`

Agrupamento de cassetes para processamento simultâneo (tambor/estufa).

- Um técnico monta o lote no fim do expediente e o conclui no dia seguinte ao retirar os blocos
- Status: `Em Andamento` → `Concluído`

---

### `Macroscopia`

Registro da descrição macroscópica feita pelo macroscopista. Um por frasco.

- `responsavel`: username do usuário que realizou a macroscopia
- `numero_cassetes`: quantidade de cassetes gerados nessa macroscopia

---

### `HistoricoMovimentacao`

**Append-only.** Nunca é alterado ou deletado. Garante rastreabilidade completa (RNF010).

Cada linha representa uma transição de status de uma entidade:

- `etapa`: em qual etapa do fluxo ocorreu (Triagem, Macroscopia, Processamento, Microscopia)
- `status_anterior` / `status_novo`: os valores do campo `status` antes e depois
- `usuario_responsavel`: username de quem executou a ação
- `ip_origem`: IP da requisição
- `timestamp_transicao`: quando ocorreu (auto)

As FKs `id_exame`, `id_frasco` e `id_cassete` são todas opcionais — apenas a que se aplica à entidade que transicionou é preenchida.

---

### `RefreshToken`

Tokens de renovação de sessão armazenados no banco.

- Invalidados após uso (rotation) e na expiração
- `groups`: grupos AD do usuário no momento da criação (usados para renovar o access token sem bater no AD novamente)
