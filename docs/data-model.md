# Modelo dos Dados e Entidades (frontend)

Última atualização: 22 Jan 2026

## API endpoints atualmente chamados
- `POST /api/login` (body form: username, password, remember_me) -> `{ access_token }`
- `POST /api/logout` (fire and forget)
- `POST /api/token/refresh` -> `{ access_token }`
- `GET /api/users/me` -> `User`
- `GET /api/pacientes` -> lista de pacientes para tabela
- `GET /api/pacientes/{codigo}` -> detalhe de paciente buscado

## Paciente
Campos atualmente usados:
| Campo | Tipo | Fonte | Observacoes |
| --- | --- | --- | --- |
| codigo | number|string | frontend/src/views/Pacientes.vue (tabela) | exibido como "Prontuario"; considere alinhar nome com `prontuario` usado em outros lugares |
| prontuario | string | Home.vue (pacienteAtual/proximoPaciente), Solicitacoes.vue, Altas.vue | identificador principal em quase todas as telas |
| nome | string | Pacientes.vue (detalhe) | |
| dt_nascimento | string | Pacientes.vue (detalhe) | string de data exibida sem formatacao |
| nome_mae | string | Pacientes.vue (detalhe) | |
| nome_pai | string? | Pacientes.vue (detalhe) | opcional |
| sexo | string | Pacientes.vue (detalhe) | valor livre |
| cor | string | Pacientes.vue (detalhe) | valor livre |
| idade | number | Home.vue, Solicitacoes.vue | derivado de dt_nascimento? atualmente mockado |
| especialidade | string | Home.vue, Solicitacoes.vue | especialidade do atendimento atual |
Sugestoes de campos uteis: contato_responsavel, alergias, risco_clinico/score, plano_de_saude, diagnostico_principal, data_admissao, data_alta_prevista, isolamento (boolean/motivo), origem_atendimento (PS, centro cirurgico etc.).

### Mock de pacientes (CSV)
- Arquivo: `data/pacientes.csv` (usado pelo `PacienteCsvProvider` quando `PACIENTE_PROVIDER_TYPE=CSV`).
- Colunas atuais do mock:
  - `codigo` (int) — chave principal, tratada como prontuario.
  - `prontuario` (string) — repetido para compatibilidade com UI.
  - `nome` (string)
  - `dt_nascimento` (YYYY-MM-DD) e `idade` (inteiro, derivado para facilitar o front)
  - `nome_mae`, `nome_pai` (string, pai opcional)
  - `sexo` (M/F), `cor` (Branca/Parda/Preta/Amarela/Indigena)
  - `especialidade_atual`, `diagnostico_principal`
  - `data_admissao`, `data_alta_prevista` (YYYY-MM-DD)
  - `origem_atendimento` (PS, cirurgico, transferido etc.)
- O CSV contem 20 pacientes diversos para testes de lista e detalhe.

## Leito
Campos atualmente usados:
| Campo | Tipo | Fonte | Observacoes |
| --- | --- | --- | --- |
| leitoNumero | string | Home.vue, BedCard.vue | identificador do leito |
| status | enum(disponivel, ocupado, higienizacao, desativado, alta) | Home.vue, StatusBadge.vue | guia comportamento/botoes |
| tipo | enum(cirurgico, hem, obstetrico, outro, nao_definido) | Home.vue | controla rotulo de cor |
| pacienteAtual | { prontuario, idade, especialidade }? | Home.vue | opcional, mostra quem ocupa |
| proximoPaciente | { prontuario, idade, especialidade }? | Home.vue | opcional, fila/reserva |
| tipoReserva | string? | Home.vue | motivo da reserva (ex: Cirurgico, Emergencia) |
| sinalizacaoTransferencia | boolean? | Home.vue, BedCard.vue | destaca leito com alerta |
| overviewCards | numbers | Home.vue | agregados: taxa ocupacao, leitos disponiveis, em uso, higienizacao, desativados, reservas pendentes |
Sugestoes de campos uteis: unidade/setor/ala, classificacao (ex: isolamento, box, coorte), equipamentos_disponiveis (respirador, monitor, bomba), tempo_desde_ultima_limpeza, previsao_liberacao, ocupacao_iniciada_em, bloqueado_motivo, responsavel_enfermagem, tags (uti fechado, covid etc.).

### Mock de leitos (CSV)
- Arquivo: `data/leitos.csv` (novo mock para simular cards de leitos).
- Colunas:
  - `leito_numero` (string) — identificador
  - `status` (disponivel, ocupado, higienizacao, desativado, alta)
  - `tipo` (cirurgico, hem, obstetrico, outro, nao_definido)
  - `paciente_prontuario`, `paciente_idade`, `paciente_especialidade` — dados do ocupante atual (vazios se disponivel)
  - `proximo_prontuario`, `proximo_especialidade` — fila/reserva opcional
  - `tipo_reserva` — motivo da reserva quando aplicavel
  - `sinalizacao_transferencia` — true/false para destacar alerta
  - `previsao_liberacao` — data estimada (YYYY-MM-DD) quando ja em alta ou reserva
- O CSV contem 10 leitos com status variados para cobrir os estados de UI.

## Solicitacao de vaga
Campos atualmente usados (mock em frontend/src/views/Solicitacoes.vue):
| Campo | Tipo | Observacoes |
| --- | --- | --- |
| id | string | identificador interno |
| prontuario | string | paciente ligado a solicitacao |
| idade | number | idade do paciente |
| especialidade | string | especialidade do caso |
| tipo | string | tipo de vaga (Cirurgico, HEM, Obstetrico etc.) |
| status | enum(Pendente, Reservado) | controla botoes: reservar, cancelar, cancelar reserva |
| turno | string | periodo do dia |
| destino | string? | leito ou setor alvo quando reservado |
Sugestoes de campos uteis: data_solicitacao, prioridade (baixa/media/alta/critica), origem_solicitante (BC, NIR, PS), responsavel_solicitante, justificativa_clinica, SLA_max_horas, reservado_em/por, cancelado_em/motivo/por, previsao_ocupacao, anexos ou exames chave.

## Alta (e destino)
Campos atualmente usados (frontend/src/views/Altas.vue):
| Campo | Tipo | Observacoes |
| --- | --- | --- |
| id | string | identificador interno |
| prontuario | string | paciente |
| leitoAtual | string | leito de origem |
| leitoDestino | string | string livre; quando contem "Pendente" indica aguardo do NIR |
| dataHora | string | timestamp textual |
| necessidadesEspeciais | string? | ex: oxigenio portatil, isolamento |
Sugestoes de campos uteis: status (solicitada, destino_definido, transferida, cancelada), responsavel (medico/enfermagem), motivo_alta (clinica, transferencia, obito), previsao_transferencia, confirmada_em, cancelada_em, alerta_transporte (UTI movel), posicao_na_fila_destino.

## Historico de acoes
Campos atualmente usados (frontend/src/views/Historico.vue):
| Campo | Tipo | Observacoes |
| --- | --- | --- |
| id | string | chave do log |
| operador | string | quem executou |
| acao | string | titulo curto |
| detalhes | string | descricao textual |
| dataHora | string | timestamp textual |
| tipo | enum(alta, reserva, destino, cancelamento, solicitacao, status) | direciona cor da badge |
Sugestoes de campos uteis: entidade (paciente/leito/solicitacao) e referencia_id, valores_anteriores/novos, criado_em (ISO), criado_por_id, terminal_ip, resultado (sucesso/erro), correlacao (request_id) para auditoria.

## Alerta do sistema
Campos atualmente usados (frontend/src/views/Alertas.vue):
| Campo | Tipo | Observacoes |
| --- | --- | --- |
| id | string | chave |
| tipo | enum(critico, aviso, info) | define estilo |
| titulo | string | resumo |
| mensagem | string | detalhe curto |
| dataHora | string | timestamp textual |
Sugestoes de campos uteis: origem (monitoramento, usuario, integracao), acknowledged (boolean) e ack_por/ack_em, vencimento/expira_em, entidade_relacionada (leito/prontuario/solicitacao), severidade_numerica, link_de_acao (rota ou endpoint).

## Indicador operacional
Campos atualmente usados (frontend/src/views/Indicadores.vue):
| Campo | Tipo | Observacoes |
| --- | --- | --- |
| titulo | string | nome do indicador |
| valor | string | valor ja formatado (ex: "42", "87%") |
| subtitulo | string | unidade/descricao curta |
| icone | componente | apenas para UI |
| tendencia | string | texto livre comparando periodo anterior |
Sugestoes de campos uteis: periodo_referencia (ex: semana atual), variacao (numero e unidade), meta (target), fonte_dados, frequencia_atualizacao, serie_temporal para graficos, status (em_linha/fora_da_meta).

## Usuario e autenticacao
Campos atualmente usados:
| Campo | Tipo | Fonte | Observacoes |
| --- | --- | --- | --- |
| username | string | auth.ts (`User`) | vindo do AD ou mock |
| groups | string[] | auth.ts | usado para `isAdmin` se contem "GLO-SEC-HCPE-SETISD" |
| givenName | string[]? | auth.ts opcional | retorno do AD |
| userPrincipalName | string[]? | auth.ts opcional | |
| title | string[]? | auth.ts opcional | cargo |
| department | string[]? | auth.ts opcional | |
| employeeNumber | string[]? | auth.ts opcional | matricula |
| accessToken | string | auth.ts | armazenado em localStorage |
| remember_me | boolean | Login.vue | decide uso de refresh |
Sugestoes de campos uteis: user_id interno, display_name, email, roles derivadas dos grupos, ultimo_login_em, expira_em para access_token, refresh_token, necessidade_de_revalidacao, permissoes explicitas para paginas (pacientes, solicitacoes, admin etc.).
