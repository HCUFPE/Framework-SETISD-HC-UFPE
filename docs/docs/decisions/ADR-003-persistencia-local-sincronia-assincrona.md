# ADR-003 — Persistência Local com Sincronização Assíncrona ao AGHU

**Status:** Aceito  
**Data:** 2026-05  
**Autores:** Grupo 8 — Desafio 6

---

## Contexto

O sistema pediátrico precisa garantir que dados clínicos não sejam perdidos em caso de instabilidade de rede ou indisponibilidade do AGHU durante a consulta. O modelo de integração precisa definir onde os dados são a fonte de verdade durante o atendimento e como a sincronização com o AGHU ocorre.

**Alternativas consideradas:**
1. Gravação direta no AGHU em tempo real — exige AGHU disponível durante toda a consulta
2. Persistência local com sincronização automática em background — complexidade de mensageria e retentativas
3. Persistência local com sincronização explícita pelo médico — simples, controlado, sem dependência em tempo real

## Decisão

Os dados da consulta são **persistidos no banco de dados local** (PostgreSQL em produção) durante todo o atendimento. A sincronização com o AGHU ocorre de forma **assíncrona e explícita**: o médico aciona a exportação ao finalizar a consulta, gerando o texto estruturado para copy-paste.

O sistema funciona de forma autônoma em relação ao AGHU — a consulta pode ser registrada, salva e finalizada independentemente da disponibilidade do sistema hospitalar.

## Consequências

**Positivas:**
- Sistema resiliente: funciona mesmo com AGHU indisponível
- Médico não perde dados em caso de falha de rede durante a consulta
- Banco local é fonte de verdade para KPIs e dashboard gerencial
- Histórico longitudinal do paciente fica disponível sem depender do AGHU

**Negativas:**
- Dados ficam duplicados (banco local + AGHU) após a sincronização
- Sem mecanismo automático de reconciliação entre as duas bases
- Se o médico não exportar, o AGHU fica desatualizado
