## Why

Conflitos entre exames (ex.: colonoscopia × exame de sangue), janelas de retorno (espirometria até 10 dias antes, INR até 72h), preparo e jejum de diabéticos hoje dependem do conhecimento da atendente. A TASK-009 do `SPEC.md` pede um detector automático baseado nas tabelas configuráveis `regras_exames` e `incompatibilidades_exames` (RF007, CARE-RF007, CARE-UC004), exibido como badges na fila.

## What Changes

- Novo detector que, para um item da fila, analisa os demais exames do mesmo prontuário e as regras do exame e devolve uma lista estruturada de `alertas` (`tipo`, `severidade`, `mensagem`).
- Tipos de alerta (contrato `TipoAlerta` de `05-interfaces.md`): `INCOMPATIBILIDADE`, `JANELA_RETORNO`, `ANTECEDENCIA_PREPARO`, `JEJUM_CLINICO`, `IDADE_MAMOGRAFIA`, `PRAZO_24H_VENCIDO`, `DUPLICIDADE`.
- Severidades: `ALTA` (violação confirmada), `MEDIA` (atenção ao agendar), `INFO` (orientação).
- Todas as regras lidas do SQLite (somente registros ativos e não excluídos); nada fixo no código.
- Testes `pytest` unitários dos cenários do CARE-RF007.
- Não expõe endpoint: o detector é usado por `GET /api/exames/fila` e `GET /api/exames/fila/{id}` na change `add-api-fila-exames`.

## Capabilities

### New Capabilities
- `alertas-exames`: detecção de incompatibilidades entre exames do mesmo prontuário, janelas de retorno, antecedência de preparo, jejum/diabético, alerta etário, prazo de 24h vencido e duplicidade.

### Modified Capabilities
(nenhuma)

## Dependências

- **TASK-004/005 (Komata) — pronta:** models `RegraExame`, `IncompatibilidadeExame`, `AcompanhamentoFila` e seed com espirometria (240h), INR (72h), mamografia (40 anos), colonoscopia × sangue, ressonância × oftalmo etc.
- **TASK-006 (Eduardo) — não bloqueante:** a edição das regras via API mudará os alertas automaticamente, pois o detector relê as tabelas.
- **TASK-007 (Eduardo) — não bloqueante:** o status `DUPLICADA` gravado pela importação vira alerta `DUPLICIDADE`; nos testes os itens são inseridos diretamente.
- **Independente** da TASK-008; ambas são consumidas pela TASK-010.

## Fora de escopo

- Sugestão automática de datas de agendamento.
- Bloqueio de ações por causa de alertas (os alertas são informativos; a decisão é da marcadora).
- Cálculo de idade real (sem `data_nascimento` no AGHU atual): o alerta de mamografia vira orientação para conferir a idade, e passa a ser verificado automaticamente se o provider passar a devolver `data_nascimento`.

## Impact

- Novo `src/controllers/alertas_controller.py` (lógica pura) e `tests/test_alertas_exames.py`.
- Sem migração, sem novas dependências.
