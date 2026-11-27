## Context

A base (branch `feat/fase-1-fundacao-aghu`) já tem o model `RegraPrioridade` (`codigo`, `nome`, `tipo_criterio`, `valor_match`, `peso`, `ativo`, `deleted_at`) e o seed com: Oncologia 100, Transplante 80, Hemodiálise 75, Nefrologia 65, Gestante/Criança/Idoso 40, Retorno `<=15` +20, Afinidade +15 e Rotina 10. O item `AcompanhamentoFila` tem `especialidade_solicitante`, `unidade_solicitante`, `grupo_prioritario_manual`, `flag_hemodialise` e `data_retorno_medico`, mas **não tem data de solicitação** (ela vem do AGHU). O AGHU/CSV não fornece data de nascimento.

## Goals / Non-Goals

**Goals:**
- Lógica pura (sem I/O), testável sem banco nem FastAPI.
- Mesmo resultado para a mesma entrada (`agora` injetado como parâmetro).

**Non-Goals:**
- Acesso a banco, endpoint e serialização (ficam em `add-api-fila-exames`).
- Cache de regras.

## Decisions

1. **Módulo `src/controllers/priorizacao_controller.py` com funções puras.**
   - `calcular_prioridade(item: dict, regras: list[dict], regras_exames: dict[str, dict], hoje: date) -> tuple[int, list[str]]`
   - `priorizar_fila(itens: list[dict], regras, regras_exames, hoje) -> list[dict]` (anexa `score_prioridade` e `motivos_prioridade` e ordena)
   - `filtrar_fila(itens_priorizados: list[dict], filtros: FiltrosFila) -> list[dict]`
   - Entradas como `dict` (não ORM) para facilitar teste e desacoplar do SQLAlchemy. O controller da fila (TASK-010) converte models em dicts.
   - Alternativa considerada: métodos no model. Rejeitada: mistura regra de negócio com persistência e foge do padrão em camadas do framework.

2. **Grupo clínico = maior peso, bônus = soma.** Garante a hierarquia Oncologia → Transplante → Hemodiálise/Nefrologia → Vulneráveis → Rotina da especificação. Somar todos os grupos deixaria Nefrologia + Hemodiálise (140) acima de Oncologia (100), contrariando a regra validada com o negócio. Os bônus (retorno, afinidade) são aditivos como no exemplo da spec ("Oncologia +40, Retorno próximo +15").

3. **Casamento por termos normalizados.** `valor_match` é separado por vírgula; cada termo e o texto do item (especialidade + unidade + grupo manual) são normalizados com `unicodedata` (sem acento, maiúsculo) e comparados por "contém". O caso especial `HEMODIALISE` também casa com `flag_hemodialise = true`. Alternativa: igualdade exata — rejeitada porque as unidades do AGHU vêm como `"ONCOLOGIA CLINICA"`, `"TRANSPLANTE RENAL"`.

4. **`ROTINA` como fallback.** A regra `GRUPO_CLINICO` com termo `ROTINA` só é aplicada quando nenhuma outra regra de grupo casou; ela é identificada pelo `valor_match`, não pelo `codigo`, para continuar configurável.

5. **`RETORNO_PROXIMO`** interpreta `valor_match` como `<=N` (regex `^\s*<=\s*(\d+)\s*$`). Valor inválido → regra ignorada com `logger.warning` (sem derrubar a fila).

6. **`AFINIDADE_EXAME`**: termos com 4+ letras da especialidade/unidade solicitante vs. termos da `unidade_executora` e `nome_exame` de `regras_exames[codigo_exame]`. Ignora palavras genéricas (`UDI`, `CLINICA`, `EXAME`, `COMPLETO`…, lista pequena em constante de normalização — não é regra de negócio). Sem regra de exame cadastrada → sem bônus.

7. **Desempate**: chave `(-score, data_solicitacao or datetime.max, id)`.

8. **Filtros** recebem um dataclass `FiltrosFila` com campos opcionais; aplicados por comparação simples sobre a lista já priorizada (a ordem é preservada por ser filtragem de uma lista ordenada).

## Risks / Trade-offs

- [Afinidade por termos pode gerar falso positivo/negativo] → regra é configurável (peso pode ir a 0) e o motivo aparece explicitamente na tela; registrar como ponto de validação com a Central.
- [Vulneráveis por idade não detectados sem `data_nascimento`] → usar especialidade (Pediatria, Geriatria, Obstetrícia) e `grupo_prioritario_manual`; quando o SQL do AGHU evoluir, adicionar critério por idade em outra change.
- [Data de referência em UTC] → `hoje` é parâmetro; a API passa a data local de Recife (UTC-3) para que o "retorno em N dias" bata com o calendário da Central.

## Migration Plan

Sem migração. Código novo, sem impacto em rotas existentes.
