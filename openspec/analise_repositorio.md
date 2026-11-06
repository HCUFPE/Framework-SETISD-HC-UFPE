# Análise do repositório IESI-AP-HC-G7 (base para o fluxo de Recepção)

## Negócio
- Sistema de Gestão Integrada de Serviços de Anatomia Patológica (SAP) – HC-UFPE/EBSERH.
- Dor: dados espalhados entre AGHU, planilhas Teams, livro de protocolo e papel → retrabalho, baixa rastreabilidade.
- Recepção hoje: recebe/confere amostras (unidades assistenciais, externas, blocos cirúrgicos), devolve amostras fora de competência, imprime ficha, cadastra em planilha/AGHU, confere congelação/urgência, assina livro de protocolo.
- Recepção no sistema: lê etiqueta AGHU (código de barras), confere dados importados, complementa; não acessa AGHU direto nem preenche etapas futuras.
- RNs: RN-01 acesso individual; RN-02 rastreabilidade imutável; RN-03 permissões por perfil; RN-04 sem duplicidade, incompletos = rascunho; RN-05 dados de paciente só para AP.

## Requisitos ligados à recepção
RF001 importação AGHU · RF002 consulta/histórico · RF003 ID interno único · RF004 consulta por código de barras/QR (etiqueta AGHU ou interna) · RF005 completude/rascunho · RF006 recebimento (confere paciente, prontuário, solicitação, exame, descrição do material, info clínica → registra data/hora/responsável, gera ID, libera etiquetas; sem etiqueta AGHU ou divergência → não conformidade + devolução) · RF008 etiqueta · RF011 urgência (marcada na recepção, destaque em todas as listas, filtro) · RF012 rastreabilidade · RF018 ficha de trabalho · RF020 não conformidade (lista padronizada + detalhamento, solicitação AGHU, exame, origem, médico solicitante, especialidade; interrompe fluxo; gera devolução) · RF021 devolução (motivo, quem devolveu, quem recebeu na origem, nova amostra) e cancelamento (só chefia/admin, motivo obrigatório; sai das filas, sem exclusão física).

## Modelo de dados relevante (04-modelo-dados.md)
- paciente, prontuario, solicitacao_aghu (codigo_solicitacao, sigla/nome_exame, especialidade, nome_solicitante, origem, unidade, informacoes_clinicas, status AGHU), item_solicitacao_aghu (numero_amostra, descricao_material, quantidade_informada).
- tipo_exame: HP, CG, CCV, CO (congelação), IHQ (complemento, não vira caso próprio).
- caso_ap: numero_interno (ex. `HP-0001/26`, sequencial por tipo/ano), status, etapa_atual, data_entrada_sap, urgente + motivo_urgencia (obrigatório se urgente), procedimento.
- Status do caso: RECEBIDO, EM_MACROSCOPIA, EM_CONGELACAO, EM_PROCESSAMENTO, EM_IHQ, IHQ_AGUARDANDO_EXTERNO, EM_MICROSCOPIA, AGUARDANDO_APROVACAO, LAUDO_CONCLUIDO, EM_ARQUIVAMENTO, ARQUIVADO, DEVOLVIDO, CANCELADO.
- Etapas: RECEPCAO, MACROSCOPIA, CONGELACAO, PROCESSAMENTO, IHQ, TRIAGEM_CITO, MICROSCOPIA, APROVACAO, ARQUIVO, EXTERNO.
- conferencia_recebimento: resultado ACEITA/REJEITADA/PENDENTE; checklist identificacao_confere, material_confere, quantidade_confere, recipiente_adequado; observacao; conferido_por/em.
- Confirmação de entrada = cria caso_ap + numero_interno + caso_etapa RECEPCAO + item_material raiz + historico_caso + audit_log.
- tipo_nao_conformidade: SEM_ETIQUETA_AGHU, IDENTIFICACAO_DIVERGENTE, QUANTIDADE_DIVERGENTE, MATERIAL_INADEQUADO, RECIPIENTE_DANIFICADO, FIXACAO_INADEQUADA, REQUISICAO_INCOMPLETA, OUTRO.
- nao_conformidade: status ABERTA/EM_TRATAMENTO/RESOLVIDA/CANCELADA.
- devolucao: unidade_origem, devolvido_por, recebido_por_nome, nova_amostra_solicitada/recebida, novo_caso_id, status AGUARDANDO_NOVA_AMOSTRA/NOVA_AMOSTRA_RECEBIDA/ENCERRADA.
- cancelamento: motivo obrigatório, só chefia/admin.
- Perfis: RECEPCAO, MACROSCOPIA, PROCESSAMENTO, IHQ, CITOTECNICO, RESIDENTE, PATOLOGISTA, ARQUIVO, GESTOR, ADMIN.
- QR/etiqueta: identificador opaco, sem dados pessoais.
- Planilha atual (aba HP) campos de recepção: Nº LAB, AGHU, QTDE Peças, ENTRADA, Urg.?, Nome, Registro, Idade, A/E (origem), Clínica, Procedimento (lista), MATERIAL. Aba "Rejeição" real: Data, Prontuário, Nº solicitação AGHU, Nº solicitação CMCE, Exame, Nome, Origem, Médico solicitante, Especialidade, Inconformidade, Detalhamento, Resolveu?.

## Inconsistências na documentação
- 03-casos-uso.md §1.3 e 04-modelo-dados.md §4 usam numeração de RF antiga (RF001=Autenticação, RF005=Confirmação de recebimento...), divergente de 02-requisitos.md.
- 03-casos-uso.md só tem o diagrama; UCs (UC003/UC004/UC005/UC006/UC009/UC025/UC026/UC027) não estão detalhados.
- SPEC.md ainda é template (objetivos/tasks genéricos: pacientes CNS/CPF, AES-256); 05-interfaces, 06-arquitetura e 07-glossário são placeholders. 06-arquitetura pede `.spec.ts` por service mas não há runner de teste no frontend.
- Pontos em aberto (00 §9): substituição da ficha física, data limite, protocolo de edição pós-homologação; reetiquetagem por item "a confirmar".

## Técnico – frontend (alvo da 1ª entrega)
- Vue 3.5.22, vue-router 4.6.3, Pinia 3.0.4, TypeScript 5.9.3 (strict, noUnused*), Vite 5.4.21, Tailwind 4.1.16 via @tailwindcss/vite (package.json ainda declara ^4.0.0-alpha.17), vee-validate 4.15.1 + @vee-validate/zod + zod 3.25.76, axios 1.13.2, @heroicons/vue 2.2.0, vue-toastification 2.0.0-rc.5. Node 24.13 / npm 11.6.
- Sem vitest/ESLint/Prettier. `vue-tsc --noEmit` passa limpo.
- Build → ../src/static/dist; proxy /api → 127.0.0.1:8000.
- Tema "Paper" em src/index.css (@theme): paper-bg #f4f3ef, text #66615b, sidebar #424242, primary #7a9e9f, info #68b3c8, success #7ac29a, warning #f3bb45, danger #eb5e28. Fonte Nunito (mas a variável é `--font-family-sans`, nome da alpha; no Tailwind 4 estável é `--font-sans` → a fonte provavelmente não aplica). tailwind.config.js é ignorado no v4 sem @config. Classes v3 como `bg-opacity-50` (LoadingIndicator) não funcionam no v4.
- Classes utilitárias: .container, .form-group, .form-label, .form-control.
- Componentes: Button (variant primary/info/success/warning/danger/default, loading, disabled; sem prop size, Pacientes.vue passa size="sm" inutilmente; Configuracoes usa variant "secondary" inexistente → cai em default), Card (slots header/footer), DataTable (headers {text,value}, items com id, slot actions, sem paginação/ordenação/slot por célula), Modal (teleport, max-w-lg fixo, ESC, slots header/footer), LoadingIndicator (store ui), ProfileDropdown, HelloWorld (sobra).
- Layout: DefaultLayout com sidebar recolhível (links hardcoded: Início, Componentes, Exemplo, Configurações), header com $route.name como título, rodapé com APP_NAME/APP_VERSION (pilar 10 do auditor). LoginLayout.
- Router: rotas /, /login, /componentes, /exemplo (Pacientes), /configuracoes; guard por meta.requiresAuth (só checa token).
- Stores: auth (token em localStorage, user com groups do AD; isAdmin = grupo GLO-SEC-HCPE-SETISD), ui (isLoading).
- services/api.ts: axios com Bearer + refresh em 401 (preservar – AGENTS.md §7).
- config/version.ts: busca /api/health para versão/títulos (fallback "Nome do Sistema").
- Padrão de view: Pacientes.vue usa api + toast + Card/DataTable/Button; Exemplos.vue mostra vee-validate (Form/Field/ErrorMessage) + zod.

## Técnico – backend (fora do escopo da 1ª entrega)
- Python 3.13 (.python-version / requires-python >=3.13), FastAPI 0.121, SQLAlchemy 2.0.44, Alembic, aiosqlite, asyncpg, ldap3, PyJWT, pytest; uv.
- src/version.py é a fonte única de versão/título (VERSION 1.0.0, SYSTEM_TITLE "Nome do Sistema").
- Camadas Router→Controller→Provider(interface + csv/postgres)→Resource; golden sample paciente.
- Security headers, handler de erro {"detail"}, auth mock/AD, refresh token, audit_log + audit_helper.
- Auditor: `audit_framework.py` quebra com NameError (ENDC sem `Colors.`, linha 39). Rodando com contorno em memória: 11/11 (100%).
- dev.sh sobe uvicorn + vite.
- Working tree: só frontend/package-lock.json modificado (flags "peer": true, efeito de npm install).
