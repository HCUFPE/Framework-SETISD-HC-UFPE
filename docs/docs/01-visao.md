# Documento de Visão

## 1. Problema e Oportunidade

**O Problema:** O HC/UFPE opera a pediatria com um processo híbrido manual/digital que gera ineficiência crítica. O médico precisa acessar o AGHU, copiar um formulário do Drive para papel, preencher manualmente, consultar a caderneta física do paciente e transcrever tudo de volta ao sistema.

**Impacto:** Consultas de 1h30 a 2h quando o objetivo clínico é de 35 a 45 minutos. O atraso não é por falta de dado clínico — é por falta de contexto histórico estruturado acessível no momento do atendimento.

**Solução Proposta:** Sistema web de gestão clínica pediátrica integrado ao AGHU que digitaliza o fluxo de atendimento de ponta a ponta: fila de espera, briefing clínico pré-consulta, formulário digital de consulta, caderneta de desenvolvimento e dashboard gerencial.

---

## 2. Partes Interessadas (Stakeholders)

| Ator | Papel | Necessidade Principal |
|---|---|---|
| Joana Lidyanne | Dona do negócio | Dashboard de métricas, histórico de condutas, prestação de contas |
| Filipe | Analista de Tecnologia | Integração com AGHU, mapeamento de endpoints |
| Camila | Analista de dados | Validação do escopo analítico e indicadores de processo |
| Médico HC | Usuário principal | Briefing completo antes da consulta; formulário digital sem retrabalho |
| Médico Satélite | Usuário secundário | Registro de atendimento e geração de ficha de referência |
| Recepção | Usuário operacional | Check-in e controle de status da fila |
| Paciente / Responsável | Beneficiário | Não precisar carregar caderneta física |

---

## 3. Escopo do Produto

### Módulos incluídos

| Módulo | Descrição |
|---|---|
| Fila de Atendimento | Lista de pacientes com status em tempo real, tipo de entrada e tempo de espera |
| Briefing Clínico | Visão consolidada do paciente antes da consulta: alertas, histórico, última antropometria, padrão de condutas |
| Formulário de Consulta | Registro digital da consulta: antropometria, anamnese, exame físico por sistema, marcos de desenvolvimento, M-CHAT-R, diagnóstico (CID-10/SID), procedimentos e encaminhamentos |
| Caderneta Digital | Histórico longitudinal de crescimento com curvas de peso, altura e IMC |
| Dashboard Gerencial | KPIs operacionais: tempo médio de consulta, taxa de encaminhamentos, alertas populacionais, CIDs mais frequentes, efetividade de encaminhamentos |
| Exportação AGHU | Geração de texto estruturado para copiar e colar na evolução do AGHU; geração de ficha de encaminhamento |

### Fora do escopo atual
- Prescrição eletrônica de medicamentos
- Prontuário legal (mantido no AGHU)
- Agendamento via WhatsApp
- Emergência pediátrica

---

## 4. Metas e Objetivos de Negócio

| Meta | Indicador | Situação Atual | Alvo |
|---|---|---|---|
| Reduzir tempo de consulta | Minutos por atendimento | 90–120 min | 35–45 min |
| Eliminar formulário em papel | Formulários digitais / total | 0% | 100% |
| Centralizar histórico do paciente | Fonte de verdade única | Fragmentado (Drive + AGHU + caderneta física) | Sistema |
| Visibilidade gerencial | Dashboard com métricas em tempo real | Nenhuma | Disponível |

---

## 5. Tipos de Entrada do Paciente

| Tipo | Descrição |
|---|---|
| Retorno | Consulta de acompanhamento agendada |
| Egresso | Alta recente, acompanhamento pós-internamento (retorno em 15–20 dias) |
| Encaminhamento Externo | Proveniente de UPA ou Unidade Básica de Saúde |
| Internação | Paciente já internado no HC |

---

## 6. Ciclo de Vida do Atendimento

```
Agendado → Aguardando → Em Atendimento → Pendente → Finalizado
```

Cada mudança de status gera registro auditável no banco de dados.
