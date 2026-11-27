## 0. Preparação

- [x] 0.1 Trazer a correção do auditor feita pelo Arthur (`git cherry-pick f8b07ad`, 1 linha em `audit_framework.py`) e verificar que `python audit_framework.py .` executa sem `NameError`

## 1. Normalização e casamento de regras

- [x] 1.1 Criar `src/controllers/priorizacao_controller.py` com função de normalização de texto (sem acento, maiúsculo) e verificar com teste unitário que `"Oncologia Clínica"` normaliza para `"ONCOLOGIA CLINICA"`
- [x] 1.2 Implementar casamento de regras `CLINICA` / `GRUPO_CLINICO` / `VULNERAVEL` (termos por vírgula, contém, caso `HEMODIALISE` + flag) e verificar com testes de casamento por especialidade, unidade, grupo manual e flag de hemodiálise
- [x] 1.3 Implementar filtragem de regras ativas (`ativo = true` e `deleted_at` nulo) e verificar com teste que regra inativa/excluída não pontua

## 2. Cálculo do score e motivos

- [x] 2.1 Implementar `calcular_prioridade` com grupo principal = maior peso, fallback `ROTINA` e bônus aditivos; verificar testes "grupos não se somam" (Nefro + Hemodiálise = 75) e "item sem grupo recebe rotina"
- [x] 2.2 Implementar bônus `RETORNO_PROXIMO` (`<=N`, inclusivo, ignora passado/ausente/valor inválido) e verificar testes de retorno em 10, 30 e -1 dias
- [x] 2.3 Implementar bônus `AFINIDADE_EXAME` por termos significativos e verificar teste Gastroenterologia × Colonoscopia (com e sem regra de exame cadastrada)
- [x] 2.4 Montar `motivos_prioridade` no formato `"<nome> +<peso>"` na ordem definida e verificar teste de que a soma dos motivos é igual ao score

## 3. Ordenação e filtros

- [x] 3.1 Implementar `priorizar_fila` com desempate `(-score, data_solicitacao, id)` e verificar testes "Oncologia supera rotina mais antiga", "desempate por data" e "execuções repetidas são idênticas"
- [x] 3.2 Verificar teste "peso alterado inverte a ordem": inserir regras em SQLite em memória, calcular, alterar peso de `ROTINA` no banco, recalcular e checar nova ordem
- [x] 3.3 Implementar `FiltrosFila` e `filtrar_fila` (exame, unidade, status operacional/higienização, município, região, TFD, busca) e verificar testes de que o filtro por região preserva score, motivos e ordem relativa, filtro TFD e busca por prontuário

## 4. Verificação

- [x] 4.1 Rodar `.venv/bin/python -m pytest -q` e confirmar todos os testes passando (37 existentes + novos)
- [x] 4.2 Rodar `python audit_framework.py .` e confirmar 100%
