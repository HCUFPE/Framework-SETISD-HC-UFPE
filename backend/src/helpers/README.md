# Helpers — Utilitários

Funções de uso geral que não pertencem a nenhuma camada específica da aplicação.

---

## `identificacao.py` — Geração de identificadores

Centraliza toda a lógica de geração de códigos e identificadores de amostras. O objetivo é que essa lógica exista em um único lugar e seja reutilizada por todos os controllers.

> **Por que centralizar?** Os identificadores seguem regras de negócio específicas (formato, sequencial, semestre). Ter essa lógica espalhada em vários controllers tornaria difícil garantir consistência e fácil introduzir bugs.

---

### Formato do número de solicitação

```
HP-0001/26.1
│   │    │ └── Semestre (1 = jan–jun, 2 = jul–dez)
│   │    └──── Ano (2 dígitos)
│   └───────── Sequencial por tipo + ano + semestre (4 dígitos com zero à esquerda)
└───────────── Prefixo do tipo de exame
```

**Prefixos por tipo:**

| Tipo | Prefixo |
|---|---|
| HP | HP |
| IHQ | IH |
| HPDerm | HD |
| CCV | CV |
| CG | CG |
| RevInt | RI |
| Congela | CO |

O sequencial é calculado consultando o maior valor existente para aquele tipo + ano + semestre no banco, garantindo que nunca haja colisão mesmo em inserções simultâneas.

---

### Formato do QR code

O QR code é uma string de texto gerada no momento da criação da amostra. A imagem QR real só é renderizada quando a impressora Zebra/Argox estiver disponível — o sistema não depende do hardware para funcionar.

```
FRASCO|550e8400-e29b-41d4-a716-446655440000|HP-0001/26.1|2026-06-22T10:30:00Z
│      │                                    │             └── Timestamp ISO 8601
│      │                                    └──────────────── Número de solicitação
│      └──────────────────────────────────────────────────── UUID da entidade
└─────────────────────────────────────────────────────────── Tipo (FRASCO, CASSETE, BLOCO, LAMINA)
```

---

### Funções disponíveis

| Função | Descrição |
|---|---|
| `gerar_numero_solicitacao(session, tipo_exame, ano, semestre)` | Próximo número sequencial para o tipo/ano/semestre |
| `gerar_qr_code(tipo, numero_solicitacao, identificador)` | Monta a string do QR code |
| `gerar_codigo_interno_frasco(numero_solicitacao)` | Código legível do frasco (`HP-0001/26.1-F1`) |
| `letra_fragmento(indice)` | Converte índice numérico em letra (0→A, 25→Z, 26→AA) |
| `semestre_de(data)` | Retorna 1 ou 2 conforme o mês da data |

---

## `sql_helper.py` — Queries SQL externas

Funções auxiliares para carregar e parametrizar queries SQL armazenadas em arquivos `.sql`.

Usadas exclusivamente pelos providers que acessam o banco AGHU (PostgreSQL), onde as queries são escritas diretamente em SQL por questões de controle e legibilidade.

| Função | Descrição |
|---|---|
| `read_sql_file(file_path)` | Lê o conteúdo de um arquivo `.sql` |
| `create_query(sql_content, params)` | Substitui placeholders `#{chave}` pelos valores do dict |

**Exemplo:**

```sql
-- arquivo: obter_paciente.sql
SELECT codigo, nome FROM agh.aip_pacientes WHERE codigo = #codigo
```

```python
sql = read_sql_file("obter_paciente.sql")
query = create_query(sql, {"codigo": 12345})
```
