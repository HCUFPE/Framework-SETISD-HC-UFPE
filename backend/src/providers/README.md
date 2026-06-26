# Providers — Acesso a Dados

Camada responsável por toda comunicação com bancos de dados. Os controllers nunca acessam o banco diretamente — eles sempre passam por um provider ou repository.

Há dois tipos de acesso a dados neste projeto, com padrões distintos:

---

## Dados externos — AGHU (PostgreSQL, somente leitura)

O AGHU é o sistema do hospital. O acesso é **somente leitura** e feito por SQL direto, sem ORM, pois não temos controle sobre o schema desse banco.

### Interface

**`interfaces/paciente_provider_interface.py`** define o contrato:

```python
async def listar_pacientes() -> List[Dict]
async def obter_paciente_por_codigo(codigo: int) -> Dict
```

### Implementações

**`paciente_postgres_provider.py`** — busca pacientes no banco AGHU via SQL. As queries ficam em arquivos `.sql` na pasta `sql/paciente/` e são carregadas em tempo de execução pelo `sql_helper`.

**`paciente_csv_provider.py`** — alternativa para desenvolvimento sem acesso à rede do HC. Lê um arquivo CSV com os dados. Ativado quando `PACIENTE_PROVIDER_TYPE=CSV` no `.env`.

A troca entre os dois provedores é feita sem alterar nenhum código — apenas a variável de ambiente `PACIENTE_PROVIDER_TYPE`.

---

## Dados próprios — App DB (SQLite/PostgreSQL, CRUD completo)

As entidades que o sistema possui (exames, frascos, cassetes, etc.) são acessadas via SQLAlchemy ORM e sessão do banco da aplicação.

Cada entidade tem seu próprio repository em `implementations/`.

### Repositories disponíveis

| Arquivo | Entidade | Operações principais |
|---|---|---|
| `exame_repository.py` | Exame | adicionar, obter, listar, dashboard |
| `frasco_repository.py` | Frasco | CRUD + fila de macroscopia + busca por solicitação/código |
| `cassete_repository.py` | Cassete | CRUD + fila de processamento + listagem por frasco/lote |
| `macroscopia_repository.py` | Macroscopia | adicionar |
| `lote_repository.py` | LoteProcessamento | adicionar, obter, listar |
| `bloco_repository.py` | BlocoParafina | CRUD + fila de corte + busca por código |
| `lamina_repository.py` | Lamina | adicionar, listar por bloco, contar por bloco |
| `historico_repository.py` | HistoricoMovimentacao | adicionar, listar com filtros |
| `paciente_local_repository.py` | PacienteLocal | adicionar, obter, buscar por CPF/CNS |

### Padrão de queries complexas

Além do CRUD básico, alguns repositories expõem queries enriquecidas para as telas operacionais — por exemplo, a fila de macroscopia retorna os dados do frasco já com nome do paciente e número de solicitação, evitando múltiplas consultas no controller:

```python
# frasco_repository.py
async def listar_pendencias_macroscopia(self) -> List[FrascoDetalhe]:
    # JOIN frasco + exame + paciente, filtra por status, ordena por FIFO
```

---

## Como os repositories recebem a sessão

A sessão do banco é injetada via FastAPI `Depends` no router e repassada ao controller, que a passa ao repository. Isso garante que toda a operação de negócio aconteça dentro da mesma transação.

```python
# Router → Controller → Repository (mesma sessão)
session: AsyncSession = Depends(get_app_db_session)
```

O commit é sempre feito no controller após todas as operações, nunca dentro do repository. Isso dá ao controller o controle sobre os limites da transação.

---

## Queries SQL externas

As queries para o AGHU ficam em `sql/paciente/`:

| Arquivo | Finalidade |
|---|---|
| `listar_pacientes.sql` | Lista pacientes da tabela `agh.aip_pacientes` |
| `obter_paciente.sql` | Busca um paciente por código |
