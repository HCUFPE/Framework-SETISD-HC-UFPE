# Interfaces e Integrações

## 1. Interfaces de Usuário (SPA Vue 3 + Tailwind)

A interface segue rigorosamente o layout padrão do `Framework-SETISD-HC-UFPE` (`DefaultLayout` com sidebar lateral à esquerda, marca institucional HC-UFPE e versão SemVer `vX.Y.Z` no rodapé; `LoginLayout` para autenticação), reutilizando os componentes `DataTable`, `Modal`, `Card`, `Button`, `LoadingIndicator` e `ProfileDropdown`.

| Rota Frontend | Tela / View | Perfil Principal | Elementos Principais |
| :--- | :--- | :--- | :--- |
| `/login` | `Login.vue` | Todos | Autenticação AD/LDAP (ou Mock `admin`/`admin`). |
| `/fila` | `FilaExames.vue` | Marcador, Gestor | Tabela priorizada com `score_prioridade` e tooltip de justificativa, badges de alertas (conflito, retorno, duplicidade, 24h vencido), barra de filtros (exame, unidade, status, **filtro geográfico Capital/RMR/Interior/TFD**), busca por prontuário/solicitação e modal de ação (iniciar 24h, confirmar agendamento no AGHU, liberar vaga, busca ativa por prontuário). |
| `/importacao` | `ImportacaoForms.vue` | Marcador, Gestor | Upload CSV/XLSX da planilha do Google Forms, pré-visualização da higienização (`Válidas`, `Duplicadas`, `Divergência de Exame`, `Não Encontradas no AGHU`) e histórico de importações. |
| `/regras` | `RegrasConfiguracao.vue` | Gestor, Admin | 3 abas editáveis: **(1) Pesos de Prioridade**, **(2) Regras por Exame** (preparo, janela de retorno, jejum, idade) e **(3) Matriz de Incompatibilidades** (Exame A × Exame B + intervalo em dias). |
| `/dashboard` | `DashboardKpis.vue` | Gestor, Admin | Cards e gráficos com KPIs (fila por exame/unidade, tempo médio de espera/resposta, taxa de confirmação 24h, erros/duplicidades barrados, recorte geográfico/TFD). |
| `/configuracoes` | `Configuracoes.vue` | Admin | Gestão de usuários/perfis RBAC com botão **"Consultar AD"** + visualização da trilha `audit_logs` (base já pronta no framework). |

---

## 2. Contrato de API REST (Backend FastAPI)

Todas as rotas de negócio seguem o **Default-Private Router Pattern** (`dependencies=[Depends(auth_handler.decode_token)]`). Exceções públicas: `POST /api/login`, `POST /api/refresh` e `GET /api/health`.

### Módulo de Fila e Exames (`/api/exames`)
* `GET /api/exames/fila` — Lista fila higienizada e ordenada por prioridade (suporta filtros `codigo_exame`, `unidade`, `status_operacional`, `status_higienizacao`, `municipio`, `regiao`, `apenas_tfd`, `apenas_24h_vencidos`, `busca`).
* `GET /api/exames/fila/{id}` — Detalhe completo do item + outros exames do mesmo prontuário + alertas de conflito/preparo/retorno.
* `PATCH /api/exames/fila/{id}/status` — Atualiza status operacional (iniciar 24h, confirmar/registrar agendamento no AGHU, marcar sem resposta/cancelado) com auditoria obrigatória.
* `PATCH /api/exames/fila/{id}/vincular-solicitacao` — Corrige solicitação inválida via busca ativa por prontuário no AGHU.
* `GET /api/exames/aghu/buscar` — Busca ativa somente-leitura no AGHU por `prontuario`, `codigo_solicitacao` ou `nome`.

### Módulo de Importação do Forms (`/api/importacoes`)
* `POST /api/importacoes/forms` — Recebe upload CSV/XLSX do Forms, executa cruzamento `Forms × AGHU` e persiste itens higienizados.
* `GET /api/importacoes` — Histórico de importações realizadas.

### Módulo de Regras Configuráveis (`/api/regras`) — *Restrito a `GESTOR_CENTRAL` / `ADMINISTRADOR`*
* `GET / POST / PUT / DELETE /api/regras/prioridades` — CRUD (soft delete) de grupos e pesos de prioridade.
* `GET / POST / PUT / DELETE /api/regras/exames` — CRUD (soft delete) de regras de preparo, retorno e alertas por exame.
* `GET / POST / PUT / DELETE /api/regras/incompatibilidades` — CRUD (soft delete) de pares incompatíveis.

### Módulo de Dashboard e Auditoria (`/api/dashboard`, `/api/admin`)
* `GET /api/dashboard/kpis` — Retorna KPIs agregados da operação.
* `GET /api/admin/audit-logs` — Consulta filtrável da trilha de auditoria imutável.

---

## 3. Integrações de Software e Hardware

* **AGHU (PostgreSQL — Somente Leitura):** Conexão assíncrona via `DatabaseManager` e `ExamePostgresProvider` executando SQL nativo (`src/providers/sql/exames/`). Em desenvolvimento offline, substituído de forma transparente por `ExameCsvProvider` lendo o CSV oficial do Drive (com normalização das aspas duplas).
* **Planilha Google Forms (Entrada de Arquivo):** Leitura passiva via upload CSV/XLSX (sem edição direta da planilha original do Drive, evitando desconfiguração por novas respostas).
* **Active Directory (AD/LDAP Ebserh):** Autenticação corporativa e pré-validação de usuários no cadastro RBAC (com fallback Mock local).
* **Hardware:** Não há integração direta com hardware; o ticket impresso (`AELR_TICKET_PACIENTE`) continua sendo emitido exclusivamente pelo AGHU sem alterações.

---

## 4. Interfaces de Integração (TypeScript)

### [SCHEMA] Contratos TypeScript do Frontend (`frontend/src/types/exames.ts`)
```typescript
export type StatusHigienizacao =
  | 'VALIDA'
  | 'DUPLICADA'
  | 'DIVERGENCIA_EXAME'
  | 'NAO_ENCONTRADA'
  | 'JA_REALIZADA';

export type StatusOperacional =
  | 'NA_FILA'
  | 'AGUARDANDO_CONFIRMACAO_24H'
  | 'CONFIRMADO_AGENDADO_AGHU'
  | 'SEM_RESPOSTA_24H'
  | 'CANCELADO';

export type TipoAlerta =
  | 'INCOMPATIBILIDADE'
  | 'JANELA_RETORNO'
  | 'ANTECEDENCIA_PREPARO'
  | 'JEJUM_CLINICO'
  | 'IDADE_MAMOGRAFIA'
  | 'PRAZO_24H_VENCIDO'
  | 'DUPLICIDADE';

export interface IAlertaExame {
  tipo: TipoAlerta;
  severidade: 'ALTA' | 'MEDIA' | 'INFO';
  mensagem: string;
}

export interface IItemFila {
  id: number;
  codigoSolicitacao: string;
  codigoExame: string | null;
  nomeExame: string | null;
  prontuario: string | null;
  nomePaciente: string;
  telefoneContato: string | null;
  municipio: string | null;
  regiaoGeografica: 'CAPITAL' | 'RMR' | 'INTERIOR' | 'NAO_INFORMADO';
  utilizaTfd: boolean;
  unidadeSolicitante: string | null;
  dataSolicitacao: string | null;
  dataRetornoMedico: string | null;
  statusHigienizacao: StatusHigienizacao;
  statusOperacional: StatusOperacional;
  scorePrioridade: number;
  motivosPrioridade: string[];
  alertas: IAlertaExame[];
  contatoIniciadoEm: string | null;
  prazoConfirmacaoEm: string | null;
  dataAgendadaAghu: string | null;
  preparoOrientado: boolean;
}

export interface IRegraPrioridade {
  id: number;
  codigo: string;
  nome: string;
  tipoCriterio: 'CLINICA' | 'GRUPO_CLINICO' | 'VULNERAVEL' | 'AFINIDADE_EXAME' | 'RETORNO_PROXIMO';
  valorMatch: string;
  peso: number;
  ativo: boolean;
}

export interface IRegraExame {
  id: number;
  codigoExame: string;
  nomeExame: string;
  unidadeExecutora: string | null;
  antecedenciaMinimaDias: number;
  janelaRetornoMaxHoras: number | null;
  exigeJejum: boolean;
  priorizarManhaDiabetico: boolean;
  idadeMinimaAlerta: number | null;
  orientacoesPreparo: string | null;
  ativo: boolean;
}

export interface IIncompatibilidadeExame {
  id: number;
  codigoExameOrigem: string;
  codigoExameConflitante: string;
  tipoConflito: 'MESMO_DIA' | 'PREPARO' | 'INTERVALO_MINIMO';
  intervaloMinimoDias: number;
  motivo: string;
  ativo: boolean;
}

export interface IKpiDashboard {
  totalNaFila: number;
  aguardando24h: number;
  prazo24hVencidos: number;
  confirmadosAgendados: number;
  duplicidadesBarradas: number;
  divergenciasDetectadas: number;
  tempoMedioEsperaDias: number;
  filaPorExame: Array<{ exame: string; quantidade: number }>;
  filaPorRegiao: Array<{ regiao: string; quantidade: number }>;
}
```
