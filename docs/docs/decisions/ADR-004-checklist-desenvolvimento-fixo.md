# ADR-004 — Checklist de Marcos de Desenvolvimento Fixo em Código

**Status:** Aceito  
**Data:** 2026-05  
**Autores:** Grupo 8 — Desafio 6

---

## Contexto

Os marcos de desenvolvimento infantil e as perguntas do M-CHAT-R (triagem de autismo para 16–30 meses) são baseados em protocolos clínicos que podem ser atualizados ao longo do tempo conforme novas diretrizes do Ministério da Saúde ou da SBP (Sociedade Brasileira de Pediatria). O sistema precisa decidir como armazenar e gerenciar essas perguntas.

**Alternativas consideradas:**
1. Tabela de configuração no banco de dados — perguntas editáveis sem novo deploy, mas exige interface de administração e validação clínica dos conteúdos
2. Arquivo de configuração externo (JSON/YAML) — editável sem recompilação, mas exige controle de versão e validação manual
3. Fixo em código — simples, versionado junto ao fonte, sem risco de edição acidental

## Decisão

Os checklists de marcos de desenvolvimento e as questões do M-CHAT-R são **definidos estaticamente no código**, baseados na caderneta de saúde da criança vigente do Ministério da Saúde. Nenhuma interface de edição será criada no escopo atual do projeto.

## Consequências

**Positivas:**
- Implementação simples, sem necessidade de motor de formulários dinâmicos
- Perguntas versionadas junto ao código — auditável via git
- Sem risco de edição acidental por usuários sem qualificação clínica
- Escopo do projeto mantido dentro do viável para o prazo

**Negativas:**
- Atualização de protocolo clínico exige novo deploy da aplicação
- Não é possível personalizar por médico ou por clínica sem alteração de código
- Dívida técnica conhecida: em versão futura, um motor de formulários configurável seria o ideal
