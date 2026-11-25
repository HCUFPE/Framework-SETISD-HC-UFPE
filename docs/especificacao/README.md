# Documentação do Projeto — Otimização da Gestão de Vagas para Exames Diagnósticos (HC-UFPE)

Este diretório contém a Especificação de Requisitos de Software (SRD / SDD) e os artefatos de análise do **Sistema Interno de Gestão de Fila e Triagem de Exames** desenvolvido pelo **Grupo 4** para a **Central de Marcação de Exames do HC-UFPE (EBSERH)**.

## 🚀 Spec-Driven Development (SDD)
Este projeto utiliza o padrão de desenvolvimento orientado a especificações auxiliado por IA do **Framework-SETISD-HC-UFPE**. A documentação abaixo atua como **contrato executável** para implementação, testes e auditoria arquitetural.

### Como Iniciar
1. **Consulte o [SPEC.md](SPEC.md)**: Ponto de entrada central com objetivos, guardrails e *Task Breakdown* ativo do MVP.
2. **Siga as Diretrizes do Framework**: Localizadas em [`AGENTS.md`](../../AGENTS.md) e [`06-arquitetura.md`](06-arquitetura.md).
3. **Padrão CARE**: Requisitos e Casos de Uso seguem o formato *Context-Action-Result-Evaluation* para garantir testabilidade.

## Estrutura de Documentos

0. [**Validação e Fluxo de Negócio**](00-validacao-negocio.md): **(Fase 0 — Negócio)** Alinhamento executivo com a Central de Marcação e SETISD, regras de negócio e matriz de decisões.
1. [**Visão**](01-visao.md): Problema, stakeholders, escopo, limites (somente leitura no AGHU, sistema estritamente interno) e metas.
2. [**Requisitos**](02-requisitos.md): Requisitos funcionais (RF), não funcionais (RNF) e detalhamento CARE.
3. [**Casos de Uso**](03-casos-uso.md): Atores, diagrama de casos de uso, fluxo TO-BE (alinhado em 06/11) e especificações CARE.
4. [**Modelo de Dados**](04-modelo-dados.md): MER completo (leitura AGHU conforme SQL/CSV do Drive + tabelas locais SQLite), dicionário e JSON Schemas.
5. [**Interfaces**](05-interfaces.md): Telas Vue 3, contratos REST da API, interfaces TypeScript e estratégia de integração (`CSV`/`PostgreSQL` + importação do Forms).
6. [**Arquitetura**](06-arquitetura.md): Stack obrigatória SETISD, segurança (AD/RBAC/LGPD), 11 pilares mandatórios e guardrails para IA.
7. [**Glossário**](07-glossario.md): Termos hospitalares, operacionais da Central e técnicos do framework.
- [**Fluxo Atual Visual (AS-IS)**](processo-atual.JPG): Mapeamento preliminar da rotina manual na Central de Marcação.

*Hospital das Clínicas da UFPE (HC-UFPE / EBSERH) — Grupo 4*
