## Resumo

<!-- O que este PR entrega e por quê, em 2 a 4 frases. -->

## Contexto

- **Issue:** <!-- número da issue, sem "#" no título do commit -->
- **Change OpenSpec:** <!-- ex.: openspec/changes/add-reception-flow (ou "não se aplica") -->
- **Requisitos e casos de uso:** <!-- ex.: RF006, RF020, RF021 — docs/especificacao/02-requisitos.md -->

## Tipo de mudança

- [ ] Nova funcionalidade
- [ ] Correção de bug
- [ ] Refatoração (sem mudança de comportamento)
- [ ] Documentação / especificação
- [ ] Infraestrutura, build ou configuração
- [ ] Mudança incompatível (quebra algo que já existe)

## O que mudou

<!-- Principais alterações, agrupadas por área (frontend, backend, docs, specs). -->

-

## Como testar

<!-- Passos para quem revisa reproduzir e validar. Inclua usuário, rota e dados de teste. -->

1.
2.
3.

## Evidências

<!-- Prints, GIFs ou saída de comandos. Use apenas dados fictícios: nada de dados reais de pacientes (LGPD). -->

## Checklist

**Conformidade com o framework (AGENTS.md)**
- [ ] `python audit_framework.py .` com 100% (11/11)
- [ ] Frontend sem erros de tipo: `npx vue-tsc --noEmit` (em `frontend/`)
- [ ] Testes do backend passando: `pytest` (quando houver mudança no backend)
- [ ] Segue a especificação em `docs/especificacao/`; divergências estão explicadas acima

**Segurança e dados**
- [ ] Nenhum segredo, senha ou DSN no código; `.env.example` atualizado se houver variável nova
- [ ] Novas rotas da API protegidas por padrão (`dependencies=[Depends(auth_handler.decode_token)]`)
- [ ] Mutações de dados clínicos ou de acesso registram auditoria (`registrar_auditoria()`)
- [ ] Sem exclusão física de registros (soft delete)
- [ ] Nenhum dado real de paciente em código, mocks, testes ou evidências

**Interface**
- [ ] Reaproveita os componentes de `frontend/src/components/` e o tema do framework
- [ ] Elementos clicáveis com cursor, hover, estado pressionado e foco visível

**Entrega**
- [ ] Versão atualizada em `src/version.py` (SemVer), se for entrega em produção
- [ ] Change OpenSpec com as tarefas concluídas (e arquivado, se for o caso)

## Pontos de atenção

<!-- Riscos, pendências, decisões tomadas durante a implementação ou dúvidas para quem revisa. -->
