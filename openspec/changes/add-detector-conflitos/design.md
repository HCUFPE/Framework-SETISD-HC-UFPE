## Context

Models prontos na base: `RegraExame` (`antecedencia_minima_dias`, `janela_retorno_max_horas`, `exige_jejum`, `priorizar_manha_diabetico`, `idade_minima_alerta`, `orientacoes_preparo`) e `IncompatibilidadeExame` (`codigo_exame_origem`, `codigo_exame_conflitante`, `tipo_conflito` `MESMO_DIA | PREPARO | INTERVALO_MINIMO`, `intervalo_minimo_dias`, `motivo`). O item da fila tem `data_retorno_medico` (date), `data_agendada_aghu`, `contato_iniciado_em`, `prazo_confirmacao_em` (datetimes UTC sem fuso) e `flag_diabetico_jejum`. O AGHU não traz data de nascimento nem data agendada.

## Goals / Non-Goals

**Goals:**
- Função pura, `agora` injetado, saída ordenada e estável.
- Mesmo detector usado na listagem (contexto só da fila local) e no detalhe (fila local + AGHU).

**Non-Goals:**
- Acesso a banco/provider (feito pelo controller da fila em `add-api-fila-exames`).
- Bloqueio de transições de status por alertas.

## Decisions

1. **Módulo `src/controllers/alertas_controller.py`** com:
   - `detectar_alertas(item: dict, outros_exames: list[dict], regras_exames: dict[str, dict], incompatibilidades: list[dict], agora: datetime) -> list[dict]`
   - Funções privadas por tipo (`_alertas_incompatibilidade`, `_alerta_janela_retorno`, …) para teste isolado e leitura fácil.
   - `outros_exames` = dicts com `codigo_exame`, `nome_exame`, `data_agendada` (opcional), `origem` (`FILA` ou `AGHU`). O controller da fila monta essa lista.

2. **Matriz consultada nas duas direções.** O seed cadastra `COLONO → HEMO`; o item de hemograma também precisa do alerta. Indexar as incompatibilidades por `frozenset({a, b})`.

3. **Distância em dias por data de calendário** (`abs((d1.date() - d2.date()).days)`), não por horas: é como a Central pensa ("2 dias de intervalo"). `MESMO_DIA` viola quando a distância é 0; `PREPARO`/`INTERVALO_MINIMO` violam quando a distância é menor que `intervalo_minimo_dias`.

4. **Janela de retorno** comparada em horas entre `data_agendada_aghu` e `datetime.combine(data_retorno_medico, time.min)`. Início do dia é a leitura conservadora (o horário da consulta não é conhecido).

5. **Antecedência de preparo** compara `data_agendada_aghu.date() - (contato_iniciado_em or agora).date()` com `antecedencia_minima_dias`.

6. **Idade**: usa `data_nascimento` do item se existir (campo opcional que o provider AGHU pode passar a devolver); senão alerta `INFO`.

7. **Severidades e ordenação**: `{"ALTA": 0, "MEDIA": 1, "INFO": 2}` e chave `(sev, tipo, mensagem)`.

8. **Mensagens** montadas a partir dos nomes cadastrados (`nome_exame`, `motivo`, `orientacoes_preparo`), sem textos clínicos fixos no código além do esqueleto da frase.

## Risks / Trade-offs

- [Lista longa de alertas `INFO` pode poluir a tela] → o front pode filtrar por severidade; a ordenação coloca `ALTA` primeiro. Combinar com o Pedro exibir só `ALTA`/`MEDIA` como badge e `INFO` no detalhe.
- [Na listagem, exames do AGHU de outros pedidos não são consultados (custo de N chamadas)] → a listagem usa só os itens da fila local; o detalhe (`GET /fila/{id}`) inclui também o AGHU. Documentado no contrato da API.
- [Horários em UTC sem fuso] → mesmo padrão usado pelos KPIs do Arthur; as comparações por dia usam a data UTC, aceitável para o MVP.

## Migration Plan

Sem migração.
