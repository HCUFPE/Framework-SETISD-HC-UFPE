# SPEC.md - Contrato de Desenvolvimento (SDD)

## 1. Visão Geral e Resultados Esperados
Este documento é a ÚNICA fonte de verdade para a orquestração do desenvolvimento. O objetivo é construir um sistema hospitalar seguro e em conformidade com a LGPD.

### Objetivos de Alto Nível
- [ ] Implementar autenticação via LDAP/AD.
- [ ] Gerenciar cadastro de pacientes (CNS/CPF).
- [ ] Garantir trilhas de auditoria imutáveis.

## 2. Contexto do Projeto (Documentação Imutável)
As definições detalhadas estão distribuídas nos seguintes documentos:
- [Visão](01-visão.md)
- [Requisitos](02-requisitos.md)
- [Casos de Uso](03-casos-de-uso.md)
- [Modelo de Dados](04-modelo-de-dados.md)
- [Interfaces](05-interfaces.md)
- [Arquitetura](06-arquitetura.md)
- [Glossário](07-glossário.md)

## 3. Limites de Escopo e Guardrails (Anti-Patterns)
**A IA DEVE:**
- Seguir rigorosamente o Modelo de Dados definido em `04-modelo-dados.md`.
- Implementar testes unitários para cada funcionalidade nova.
- Utilizar criptografia AES-256 para dados sensíveis.

**A IA NÃO DEVE:**
- Criar dependências externas não documentadas em `06-arquitetura.md`.
- Implementar exclusão física de registros (usar Soft Delete).
- Burlar o sistema de RBAC (Role-Based Access Control).

## 4. Task Breakdown (Plano de Implementação)
### Fase 1: Infraestrutura e Dados
- [ ] [TASK-001] Validar esquemas de banco de dados conforme `04-modelo-dados.md`.
- [ ] [TASK-002] Configurar ambiente de auditoria de logs.

### Fase 2: Funcionalidades Essenciais
- [ ] [TASK-003] Implementar Módulo de Autenticação (RF001).
- [ ] [TASK-004] Implementar Cadastro de Pacientes (RF002).

## 5. Critérios de Verificação Global
- [ ] 100% de cobertura em rotas de autenticação.
- [ ] Zero vulnerabilidades críticas no lint de segurança.
- [ ] Conformidade total com os esquemas JSON/OpenAPI.