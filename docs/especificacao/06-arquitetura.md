# Arquitetura e Segurança

## 1. Stack Técnica
* Front-end, Back-end e Banco de Dados.

## 2. Conformidade LGPD
* Anonimização e gestão de consentimento (TCLE).

## 3. Acessos
* RBAC e MFA.

## 4. Guardrails para IA (SDD)
Para manter a integridade sistêmica, os assistentes de IA devem aderir às seguintes restrições:

### Escopo Positivo (O que fazer)
- **Documentação de Código**: Comentar funções complexas seguindo o padrão JSDoc/TSDoc.
- **Tratamento de Erros**: Utilizar blocos try-catch com logs de erro padronizados.
- **Testes**: Criar um arquivo de teste `.spec.ts` para cada novo controller ou service.

### Escopo Negativo (O que NÃO fazer - Anti-Patterns)
- **No Hard Deletes**: Proibido o uso de `DELETE` SQL. Utilizar coluna `deleted_at`.
- **No Secrets in Code**: Proibido salvar chaves de API ou senhas no código; utilizar `.env`.
- **No Refactoring Unasked**: Não alterar arquivos de infraestrutura ou configuração global sem instrução explícita no `SPEC.md`.