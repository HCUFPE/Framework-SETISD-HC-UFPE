# Interfaces e Integrações

## 1. Telas do Sistema

### 1.1 Fila de Atendimento (`/`)
Listagem de pacientes do dia. Cada linha exibe nome, idade, prontuário, tipo de entrada (badge colorido), status e tempo de espera. Ação principal: selecionar paciente → abre Briefing Clínico.

### 1.2 Briefing Clínico (`/briefing`)
Visão pré-consulta dividida em dois painéis:
- **Painel esquerdo:** Linha do tempo das últimas consultas (HC + externos) e padrão de condutas (CIDs frequentes, encaminhamentos sem retorno, internações).
- **Painel direito:** Alertas ativos com badge de categoria e nível (crítico/atenção) e últimos dados antropométricos com sparkline de evolução do peso.
- **Header:** Nome do paciente, tipo de entrada, idade, prontuário, botões de ação (Iniciar/Continuar Atendimento, Ver Caderneta Digital, Ver Prontuário Completo).

### 1.3 Formulário de Consulta (`/consulta`)
Barra superior fixa: nome do paciente, badge "Consulta em andamento", timer em tempo real (formato HH:MM:SS), botões "Salvar Rascunho" e "Finalizar Atendimento".

Abas:
| Aba | Condicional |
|---|---|
| Antropometria | Sempre |
| Anamnese | Sempre |
| Exame Físico | Sempre |
| Marcos | Sempre |
| M-CHAT-R | Apenas para `ageInMonths` entre 16 e 30 |
| Encaminhamentos | Sempre |

Seções fixas abaixo das abas: Diagnóstico (CID-10 + SID), Procedimentos Realizados (colapsável via switch), Dados de Atendimento Externo (colapsável).

Barra inferior fixa: "Salvar Rascunho" e "Copiar para AGHU e Finalizar".

### 1.4 Caderneta Digital (`/caderneta`)
Curvas longitudinais de crescimento (peso, altura, IMC) com percentis e marcos de desenvolvimento registrados em consultas anteriores.

### 1.5 Dashboard Gerencial (`/dashboard`)
- Filtro de período: 7/30/90 dias.
- KPIs (cards): Consultas realizadas, Tempo médio de consulta (com meta), Taxa de encaminhamentos, Formulários incompletos, Taxa de retorno de encaminhamentos, Alertas de negligência.
- Gráfico de barras: Consultas por tipo de entrada por semana.
- Gráfico de linha: Tempo médio de consulta por semana vs. meta de 45 min.
- Gráfico de barras horizontal: CIDs mais frequentes no período.
- Tabela: Efetividade de encaminhamentos por especialidade (% retorno em verde/âmbar/vermelho).
- Tabela filtrável: Alertas populacionais por categoria.

---

## 2. API — Endpoints Implementados

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/login` | Login com credenciais LDAP. Retorna JWT; seta cookie refresh token se `remember_me=true`. |
| POST | `/api/token/refresh` | Renova JWT usando refresh token do cookie HttpOnly. Rotaciona o refresh token. |
| POST | `/api/logout` | Invalida refresh token e apaga cookie. |
| GET | `/api/users/me` | Retorna dados do usuário autenticado (grupos do AD incluídos). |

### Pacientes

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/pacientes` | Lista pacientes da fonte configurada (CSV ou PostgreSQL). |
| GET | `/api/pacientes/{codigo}` | Obtém paciente pelo código. |

### Módulos auxiliares (placeholders em expansão)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/aih` | Lista AIHs (Autorização de Internação Hospitalar). |
| GET | `/api/bpa` | Lista BPAs (Boletim de Produção Ambulatorial). |

---

## 3. Integração AGHU

A integração com o AGHU opera em dois modos:

### Modo atual — Copy-paste estruturado
O sistema gera um texto pré-formatado com todos os dados da consulta que o médico copia e cola no campo de evolução do AGHU. A assinatura digital (Certbr) é feita pelo médico diretamente no AGHU após a colagem.

**Estrutura do texto gerado:**
```
╔══════════════════════════════════════════════════════╗
║       ATENDIMENTO PEDIÁTRICO — HC/UFPE               ║
╚══════════════════════════════════════════════════════╝

Paciente  : [Nome]
Prontuário: [Número]   DN: [Data de Nascimento]
Data      : [Data]
Tipo      : [Tipo de Entrada]  Duração: [HH:MM]

── ANTROPOMETRIA ────────────────────────────────────
── ANAMNESE ─────────────────────────────────────────
── EXAME FÍSICO ─────────────────────────────────────
── DIAGNÓSTICO ──────────────────────────────────────
── MARCOS DO DESENVOLVIMENTO ────────────────────────
── TRIAGEM M-CHAT-R ─────────────────────────────────  (se aplicável)
── ENCAMINHAMENTOS ──────────────────────────────────
── PROCEDIMENTOS REALIZADOS ─────────────────────────
── ALERTAS ATIVOS ───────────────────────────────────
── DADOS DE ATENDIMENTO EXTERNO ─────────────────────  (se houver)
```

### Modo futuro — Provider AGHU
Quando a API do AGHU estiver disponível (mapeamento a cargo de Filipe), a estratégia no roteador é trocada de `"csv"` para `"aghu"` sem alteração na lógica de negócio:

```python
# src/routers/paciente.py
STRATEGY = "aghu"  # trocar de "csv" para "aghu"
```

A interface `PacienteProviderInterface` garante que o controller não precisa mudar.

---

## 4. Interface de Integração (TypeScript — Frontend)

```typescript
interface IAtendimentosApi {
  login(username: string, password: string, rememberMe: boolean): Promise<{ access_token: string }>
  refreshToken(): Promise<{ access_token: string }>
  logout(): Promise<void>
  getMe(): Promise<UserInfo>
  getPacientes(): Promise<Paciente[]>
  getPaciente(codigo: number): Promise<Paciente>
}
```

---

## 5. Hardware

- Impressoras para ficha de encaminhamento (impressão via copy-paste em editor de texto).
- Estações de trabalho com navegador moderno (Chrome/Firefox/Edge).
- Acesso à rede interna do HC para autenticação LDAP.
