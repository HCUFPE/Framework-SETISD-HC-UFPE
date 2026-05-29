# ADR-001 — Adoção do Modelo Nygard para Registro de Decisões Arquiteturais

**Status:** Aceito  
**Data:** 2026-05  
**Autores:** Grupo 8 — Desafio 6

---

## Contexto

Projetos de software acumulam decisões técnicas ao longo do tempo. Sem registro formal, o raciocínio por trás de cada escolha se perde, dificultando manutenção, onboarding de novos membros e revisões futuras. O grupo precisava de uma prática leve e padronizada para documentar decisões arquiteturais.

## Decisão

Adotamos o modelo de **Architecture Decision Record (ADR)** no formato proposto por Michael Nygard, composto por:

- **Título** — identificador e nome da decisão
- **Status** — Proposto / Aceito / Depreciado / Substituído
- **Contexto** — situação que motivou a decisão
- **Decisão** — o que foi decidido
- **Consequências** — impactos positivos e negativos da decisão

Os arquivos ADR são versionados junto ao código-fonte em `docs/documentacao/decisions/`.

## Consequências

**Positivas:**
- Decisões arquiteturais ficam rastreáveis e justificadas
- Novos integrantes entendem o histórico de escolhas sem depender de memória do time
- Formato simples — cada ADR cabe em uma tela

**Negativas:**
- Exige disciplina do time para criar ADRs no momento da decisão, não depois
- ADRs desatualizados podem gerar confusão se o status não for mantido
