# Controllers — Lógica de Negócio

Os controllers orquestram as operações de negócio. Eles ficam entre os routers (que recebem a requisição HTTP) e os repositories (que acessam o banco). Cada controller contém as regras de negócio da sua etapa do fluxo.

Nenhum controller acessa o banco diretamente — isso é responsabilidade dos repositories em `providers/implementations/`.

---

## Arquivos

### `triagem_controller.py` — Recepção de amostras

Gerencia a entrada de novas amostras no sistema.

**`registrar_recebimento()`**
- Valida os dados do paciente (CPF ou CNS obrigatório)
- Valida o tipo de exame (HP, IHQ, HPDerm, etc.)
- Busca ou cria o paciente no cache local
- Gera o número de solicitação (`HP-0001/26.1`) sequencial por tipo, ano e semestre
- Cria o Exame e o Frasco associado, com QR code e código interno
- Registra o histórico de movimentação para ambos
- Devolve os dados do exame, frasco e payload de etiqueta (para impressão futura)

**`encaminhar_para_macroscopia()`**
- Transiciona o Frasco de `Na Recepção` para `Aguardando Macroscopia`
- O Exame permanece em `Na Recepção` até a macroscopia ser iniciada

**`obter_etiqueta_frasco()`**
- Retorna os dados de etiqueta de um frasco para reimpressão

---

### `macroscopia_controller.py` — Etapa de macroscopia

**`listar_pendencias()`**
- Retorna a fila da estação: frascos em `Aguardando Macroscopia` ou `Em Macroscopia`

**`buscar_frasco()`**
- Busca manual por número de solicitação ou código interno
- Substitui o leitor de QR code enquanto o hardware não está disponível

**`iniciar_macroscopia()`**
- Transiciona Frasco → `Em Macroscopia`
- Transiciona Exame → `Em Macroscopia` (em paralelo)

**`registrar_macroscopia()`**
- Valida que o frasco está em `Em Macroscopia`
- Salva a descrição e o número de cassetes
- Gera os cassetes (letras A, B, C...) com seus respectivos QR codes
- Transiciona Frasco → `Processamento Completo`
- Transiciona Exame → `Em Processamento`
- Devolve os cassetes e payloads de etiqueta

---

### `processamento_controller.py` — Processamento técnico

**`listar_pendencias()`**
- Fila de cassetes com status `Aguardando Processamento`

**`iniciar_lote()`**
- Agrupa N cassetes em um `LoteProcessamento`
- Transiciona cada cassete para `Em Processamento`

**`concluir_lote()`**
- Marca o lote como concluído
- Gera um `BlocoParafina` para cada cassete (código: `HP-0001/26.1-A`)
- Se todos os cassetes do exame estiverem concluídos, avança o Exame para `Em Microscopia`

**`gerar_laminas()`**
- Gera N lâminas para um bloco (código: `HP-0001/26.1-A-L1`)
- Avança o bloco para `Aguardando Microscopia`

**`listar_blocos_pendentes()`** / **`buscar_bloco()`**
- Fila de blocos aguardando corte microtômico e busca manual

---

### `exame_controller.py` — Consultas de exames

Consultas gerais sem lógica transacional.

- **`listar_exames()`** — todos os exames, mais recentes primeiro
- **`obter_exame()`** — um exame por ID (404 se não encontrado)
- **`listar_dashboard()`** — exames com nome do paciente e flag de SLA (atrasado se ≥ 20 dias desde a recepção)

---

### `historico_controller.py` — Rastreabilidade

**`listar_historico()`**
- Exige ao menos um filtro: `id_exame`, `id_frasco` ou `id_cassete`
- Retorna todas as transições de status em ordem cronológica
- Cada entrada registra: etapa, status anterior/novo, usuário responsável, IP e timestamp

---

### `paciente_controller.py` — Consulta de pacientes

Delega diretamente ao provedor de dados (PostgreSQL/AGHU ou CSV). Não contém lógica de negócio própria.

---

## Padrão de uso nos routers

```python
# O router recebe a requisição, extrai os dados e delega ao controller
@router.post("/")
async def registrar(dados: ExameCreate, session: AsyncSession = Depends(...)):
    return await triagem_controller.registrar_recebimento(session, dados, usuario, ip)
```

Os controllers sempre recebem a `session` do banco como primeiro argumento, seguida dos dados da operação e do `usuario`/`ip` para auditoria.
