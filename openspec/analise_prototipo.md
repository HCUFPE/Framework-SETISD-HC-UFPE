# Análise do protótipo — Sistema de Gestão Integrada de Serviços de Anatomia Patológica (HC-UFPE / EBSERH)

> Fonte: artifact `https://claude.ai/artifact/BVP8vjBHf3W5t4Bdna7mUm` (lido em modo somente leitura; versão `1793759485-b0ba`, 655 KB).
> O artifact é uma página empacotada ("Bundled Page"): manifesto base64+gzip com 9 assets. Foram extraídos e analisados:
> - `template.html` (325 KB): markup declarativo (`<x-dc>`, `<sc-if>`, `<sc-for>`, `<sc-raw-table>`…) + classe `Component extends DCLogic` com **todo o estado, regras e handlers** (~800 linhas).
> - `418268b3…js` (37 KB): módulo `window.AP` com constantes, helpers de formatação, web components (`<ap-icon>`, `<ap-barcode>`) e a função `seed()` com **todos os dados mockados**.
> - `8c1eb9ae…js`: runtime "dc-runtime" (motor do template, gerado pelo Claude Design); React 18.3.1 + ReactDOM 18.3.1 (UMD); 5 fontes woff2 (Nunito).
>
> Não há roteamento por URL: a navegação é por estado (`state.screen`). Todos os dados vivem em memória (`state.db`, recriado por `AP.seed(Date.now())` a cada carga — datas são relativas a "agora").

---

## 1. Visão geral e mapa de navegação

### 1.1. Propósito
Rastrear o caso de anatomia patológica (AP) desde a recepção da amostra (vinda de uma solicitação do **AGHU**) até o arquivamento, passando por macroscopia, congelação, processamento técnico, IHQ, microscopia (residente) e aprovação/laudo (patologista). Inclui não conformidades/devoluções, solicitações complementares (retrabalho), impressão de etiquetas/ficha/laudo, painéis de acompanhamento, indicadores, configurações e auditoria.

### 1.2. Login
- Tela centralizada (max 440px): logo quadrado verde "AP", título "Sistema de Gestão Integrada de Serviços de Anatomia Patológica", subtítulo "Hospital das Clínicas da UFPE · Serviço de Anatomia Patológica".
- Campos: **Usuário da rede** (placeholder `nome.sobrenome`, ajuda "Use seu login da rede Ebserh") e **Senha** (password). Botão **Entrar**.
- Validações/mensagens (caixa vermelha `role=alert`):
  - usuário vazio ou senha com < 4 caracteres → "Usuário ou senha inválidos. Confira os dados e tente novamente."
  - login não cadastrado ou inativo → "Seu usuário não tem acesso a este sistema. Solicite acesso à chefia da unidade." (simula Etapa 2 do modelo AD + RBAC local).
- Ao entrar: perfil ativo = primeiro perfil do usuário; tela inicial por perfil (`home`): recepção → **Recepção de amostras**; gestor → **Painel de processos**; admin → **Configurações**; demais → **Minha fila**. Grava auditoria `Segurança / Login realizado`.
- Rodapé de ajuda do protótipo lista usuários: `ana.recepcao`, `marcos.macro`, `carla.residente`, `bruno.patologista`, `fernanda.chefia`, `rafael.admin` (qualquer senha ≥ 4); `sandra.moura` demonstra usuário inativo.

### 1.3. Perfis (`AP.ROLES`) e usuário de demonstração
| id | Rótulo | Usuário padrão |
|---|---|---|
| `recepcao` | Recepção | ana.recepcao (Ana Lúcia Recepção) |
| `macroscopia` | Macroscopia | marcos.macro |
| `processamento` | Processamento técnico | paula.proc |
| `ihq` | IHQ | ivan.ihq |
| `citotecnico` | Citotécnico | rita.cito |
| `residente` | Médico residente | carla.residente |
| `patologista` | Patologista / Preceptor | bruno.patologista |
| `arquivo` | Arquivo | jose.arquivo |
| `gestor` | Gestor / Chefia | fernanda.chefia |
| `admin` | Administrador | rafael.admin |

O topo tem um seletor **"Visualizar como"** que troca o perfil livremente (recurso de protótipo; toast info "Visualizando como X."). Se o usuário logado não tem o perfil selecionado, `me()` passa a ser o usuário padrão do perfil.

### 1.4. Menu lateral (por perfil)
Grupos e itens (montados em `vShell`):
- **Trabalho**
  - *Recepção de amostras* (ícone `scan-barcode`) — **somente perfil Recepção**; badge = nº de solicitações AGHU com status `Solicitado`.
  - *Minha fila* / *Aguardando minha aprovação* (patologista) — perfis operacionais (macroscopia, processamento, ihq, citotecnico, residente, patologista, arquivo); badge = casos na etapa do perfil.
  - *Consulta de casos* (`search`) — **todos os perfis**.
- **Acompanhamento**
  - *Pendências e alertas* (`list-todo`) — todos.
  - *Painel de processos* (`square-kanban`) — todos.
  - *Indicadores* (`chart-column`) — gestor, admin, patologista.
  - *Rejeições e devoluções* (`undo-2`) — **todos os perfis**.
- **Administração**
  - admin: *Configurações* (`settings`), *Auditoria* (`shield-check`).
  - patologista: *Máscaras de texto* (`file-pen-line`, abre Configurações só com a aba de máscaras).

Controle de acesso por tela (`screenAllowed`): `recepcao` só Recepção; `fila` só perfis operacionais; `kpis` gestor/admin/patologista; `config` admin/patologista; `auditoria` admin; tela de etapa só o "dono" da etapa. Fora disso aparece a tela **"Esta área não faz parte do perfil X"** (ícone `shield-x`, texto "Cada perfil só vê e só executa o que é dele…", botão "Ir para o início").

Perfil **Gestor** tem dados de paciente ocultados (nome, prontuário, nº AGHU → "Oculto"/"Oculto para o perfil Gestor").

### 1.5. Mapa de telas (`state.screen`)
```
login
└─ app (shell: sidebar + topbar + main)
   ├─ recepcao      Recepção de amostras (stepper 4 passos)          [Recepção]
   ├─ fila          Minha fila (por perfil)                           [operacionais]
   │   └─ etapa     Formulário da etapa (macro, proc, cong, ihq, micro, triagem, aprovação, arquivo)
   ├─ consulta      Consulta e pesquisa de casos                      [todos]
   │   └─ caso      Detalhe do caso (stepper + 12 abas)               [todos]
   ├─ pendencias    Pendências e alertas                              [todos]
   ├─ kanban        Painel de processos                               [todos]
   ├─ kpis          Indicadores                                       [gestor, admin, patologista]
   ├─ devolucoes    Rejeições e devoluções                            [todos]
   ├─ config        Configurações (5 abas) / Máscaras                 [admin / patologista]
   ├─ auditoria     Auditoria                                         [admin]
   └─ forbidden     Acesso não permitido
Modais: nc (não conformidade+devolução), comp (solicitação complementar), cancel, confirm,
        devolver (parecer ao residente), print (etiqueta/ficha/laudo), saida (retirada de material)
```
Breadcrumb no topo (`crumbs`): "Trabalho", "Acompanhamento", "Administração", "Consulta de casos" (no detalhe) etc. + título da página (`pageTitle`). `document.title` = "<título> · Gestão de Anatomia Patológica".

### 1.6. Shell (layout)
- **Sidebar** (264px expandida / 72px recolhida; sticky, altura 100vh; recolhe automaticamente se `innerWidth < 1024` na carga): cabeçalho com nome do sistema (ou logo "AP" quando recolhida), grupos com título em caixa alta 12px, item ativo com fundo `#e8f1e4`, texto `#285419` e barra vertical verde de 3px à esquerda; badges de contagem em pílula cinza. **Rodapé com versão `v0.1.0`** + botão recolher/expandir (`panel-left-close`/`panel-left-open`).
- **Topbar** (64px, sticky): breadcrumb + título; **campo global de leitura** "Ler código ou buscar caso (F2)" (ícone `scan-barcode`, 44px, borda verde/vermelha piscando conforme sucesso/erro, mensagem flutuante abaixo); botão **"Simular leitura"** (menu com códigos de exemplo); seletor "Visualizar como"; sino de **notificações** com badge vermelho (IHQ externas sem resultado; casos estagnados); avatar com iniciais → menu (nome, login · lotação, perfis, **Sair**).
- **Banner AGHU indisponível** (amarelo) quando simulado: "AGHU indisponível no momento. Operações internas continuam funcionando. A recepção de novas amostras está bloqueada." + botão "Simular retorno do AGHU".
- **Main**: padding 24/32px, largura máx. 1440px (sem limite em kanban, consulta, caso e kpis).
- **Toasts**: canto superior direito (top 76px, largura 380px), ícone colorido + texto + botão fechar. success/info somem em 4s, warning em 6s, **error fica até fechar**. Também alimentam região `aria-live`.
- **Skeleton**: carregamento inicial (sidebar + blocos shimmer) e "loading" de 450ms ao navegar para fila/consulta/kanban/kpis/pendências/devoluções.

### 1.7. Leitura global de código (F2) — `doScan`
Normaliza (trim + maiúsculas) e:
1. Se é nº de solicitação AGHU com status `Solicitado`:
   - AGHU indisponível → erro "AGHU indisponível no momento. Não é possível receber a solicitação X agora."
   - perfil ≠ recepção → erro "A solicitação AGHU X ainda não foi recebida no SAP. Leve o material à recepção."
   - recepção → abre Recepção no passo 2 (conferência) — "Solicitação AGHU X carregada para conferência."
2. Senão procura caso por nº interno ou nº AGHU; ou item (bloco/lâmina) pelo padrão `^([A-Z]{2}-\d{4}\/\d{2})-(.+)$`.
3. Não achou → erro "Nenhum registro encontrado para o código X. Confira a etiqueta ou digite o número."
4. Se o perfil é dono da etapa atual e não é item → abre o formulário da etapa e **registra a chegada** ("X lido · Etapa. Chegada registrada.").
5. Caso contrário abre o detalhe do caso (aba Materiais com o item destacado em amarelo, se for item).

Códigos de "Simular leitura": `4830112` (AGHU · nódulo de mama a receber), `4830245` (paciente externo), `4830301` (congelação), `4830377` (líquido pleural), `HP-0011/26` (urgente em macroscopia), `HP-0010/26` (rascunho incompleto), `HP-0012/26-A` (bloco de caso estagnado), `HP-0006/26-B-02` (lâmina de recorte), `IH-0002/26` (IHQ externa aguardando), `HP-0001/26` (arquivado), `9999999` (inexistente).

### 1.8. Atalhos de teclado
- **F2**: foca o campo global de leitura.
- **Esc**: fecha modais de formulário (nc, comp, devolver, print, saida) e menus suspensos.
- **Ctrl/⌘+S**: salva rascunho na tela de etapa.
- **Ctrl/⌘+Enter**: conclui etapa; **na Recepção passo 3, confirma a entrada**.

---

## 2. Design system observado

### 2.1. Stack do protótipo
- Runtime "dc-runtime" (Claude Design) sobre **React 18.3.1** — template declarativo com bindings `{{ }}`, `sc-if`, `sc-for`, `sc-camel-on-*`, estilos inline (`style`, `style-hover`, `style-focus`). **Não é Vue nem Tailwind** — tudo deve ser reescrito em Vue 3 + Tailwind.
- Ícones: **Lucide 0.460.0** (UMD via unpkg) encapsulado no web component `<ap-icon name size>` (stroke 2 para ≤16px, 1.75 acima). Para Vue: `lucide-vue-next`.
- Código de barras: `<ap-barcode value height width>` — **falso** (barras derivadas dos char codes, não é Code128 real).
- Fonte **Nunito** (400/600/700/800), base 15px / line-height 22px.
- `lang="pt-BR"`, datas `dd/mm/aaaa hh:mm`.

### 2.2. Paleta (tokens extraídos)
| Papel | Cor |
|---|---|
| Primária (verde institucional) | `#336a20` · hover `#285419` · texto ativo `#285419` · fundos claros `#e8f1e4` (hover/ativo menu, chips), `#f1f7ee` (checkbox marcado) |
| Texto principal | `#1f2933` |
| Texto secundário | `#52606d` · terciário/ícones vazios `#6b7785` |
| Bordas de card/tabela | `#d5dbe1` |
| Borda de input | `#8a96a3` |
| Fundo da página / cabeçalho de tabela | `#f5f7f9` |
| Neutro (badges) | bg `#eceff2` / fg `#3e4c59` |
| Info (azul) | bg `#e6eef8` / fg `#2f5a94`; acento `#4a75b5`; **campo somente leitura AGHU** bg `#eaf0f8`, borda `#c9d7ea` |
| Sucesso | bg `#e3f0dc` / fg `#2b5a1b` |
| Atenção | bg `#fff1cc` / fg `#7a4f00`; acento `#b57900` |
| Crítico/erro/urgente | bg `#fbe3e4` / fg `#8f1f24`; acento `#b2292e` |
| Links | `#2f5a94` |

Categorias semânticas centralizadas em `AP.CAT`: `info`, `warn`, `ok`, `neutral`, `crit`.

### 2.3. Tipografia e medidas
- H1 de página 24/32 (700); H2 de seção 20/28; título da topbar 18/24 (700); rótulos 14px 600; ajuda/erros 13px; cabeçalho de grupo do menu 12px caixa alta, `letter-spacing .04em`.
- Números/códigos com `font-variant-numeric: tabular-nums` e `letter-spacing .02em`.
- Raios: 6px (inputs, botões), 10px (cards, modais, menus), 999px (pílulas/badges).
- Alturas: botões 40px (secundários pequenos 32px), inputs 40px, campo de leitura 44px (topbar) / **56px (recepção)**, linhas de tabela 44px.
- Sombra de overlay: `0 8px 24px rgba(16,24,40,.14)`. Foco: `outline 2px #336a20` / `box-shadow 0 0 0 3px rgba(51,106,32,.25)`.
- Animações: `apshim` (skeleton), `appulse` (etapa atual no stepper), `apspin`; respeita `prefers-reduced-motion`.

### 2.4. Componentes reutilizáveis observados
- **Botão primário** (verde cheio, texto branco 700), **secundário** (contorno verde), **destrutivo** (contorno ou cheio `#b2292e`), **link** (sem borda, verde ou azul sublinhado), **ícone** (32–40px transparente com hover `#f5f7f9`).
- **Badge de status** (pílula 24px, ícone 14 + rótulo, cores por `statusStyle`).
- **Badge URGENTE** (pílula vermelha cheia `#b2292e`, texto branco 800, ícone `triangle-alert`).
- **Indicadores** (pílulas): *Rascunho* (`pencil-line`, warn), *Estagnado* (`hourglass`, warn), *Retrabalho* (`rotate-ccw`, info).
- **Badge de prazo** (`AP.span`): texto "N h de P dias" / "N de P dias" / "N de P min"; nível ok (<80%), warn (≥80%), over (>100%) com ícones `circle-check`/`clock`/`triangle-alert`.
- **Segmented control Sim/Não** (botões colados; "Sim" de urgência fica vermelho, demais selecionados verdes).
- **Cards de seleção (radio)** — ex.: tipo de exame (sigla em negrito + nome).
- **Checkbox em card** (borda/fundo verdes quando marcado, altura mínima 44px).
- **Campo somente leitura AGHU**: caixa azul-clara com tag "🔒 AGHU" no canto direito.
- **Stepper horizontal** (círculos numerados 28px + linha; concluído = ✓ verde).
- **Tabela** (`border-collapse`, cabeçalho cinza `#f5f7f9`, linhas 44px, barra lateral vermelha 4px `inset box-shadow` em linhas urgentes, linha clicável com hover).
- **Chips de filtro** removíveis (verde claro) + "Limpar filtros".
- **Resumo de erros** no topo do formulário (caixa vermelha com lista de links que focam o campo) + erro inline sob cada campo (ícone `circle-alert` 14 + texto 13px vermelho) + borda vermelha.
- **Estado vazio** (ícone 48px cinza, título, subtítulo).
- **Modais**: pequeno (480px, `alertdialog`, centralizado) e de formulário (720px, alinhado ao topo com rolagem); overlay `rgba(31,41,51,.45)`.
- **Pré-visualização de impressão** em tela cheia (fundo cinza, barra superior com Fechar/Imprimir; CSS `@media print` imprime só `[data-print-root]`).
- **Toasts**, **menus suspensos** (380px), **painel de notificações**.

### 2.5. Responsividade
Não há media queries de layout; usa grids `auto-fit/auto-fill minmax(...)`, `flex-wrap` e `overflow-x:auto` em tabelas; sidebar recolhida abaixo de 1024px na carga. Foco é desktop de bancada (leitor de código de barras).

### 2.6. Acessibilidade
`aria-live` para mensagens, `aria-current` no menu e no stepper, `role=radiogroup/radio`, `aria-pressed` em toggles, `role=alert` em erros, `role=tablist/tab`, `role=tree` nos materiais, labels associados aos campos.

---

## 3. Recepção de amostras (DETALHADO)

**Tela:** `screen='recepcao'` · título "Recepção de amostras" · subtítulo "Leia a etiqueta do AGHU no frasco, confira o material e confirme a entrada." · largura máx. 1200px.
**Ator:** perfil **Recepção** (exclusivo). Outros perfis que lerem um nº AGHU recebem erro orientando levar à recepção.
**Objetivo:** transformar uma solicitação AGHU (`Solicitado`) em um **caso interno** (`HP-0001/26` etc.) após conferência física, ou registrar não conformidade + devolução.

### 3.1. Estrutura
1. Cabeçalho (H1 + subtítulo).
2. **Stepper** de 4 passos (card branco, grid 4 colunas): `1 Ler etiqueta AGHU` → `2 Conferir` → `3 Completar e confirmar` → `4 Etiquetas e ficha`. Passo atual e concluídos em verde (concluído mostra ✓), futuros brancos com borda cinza; linhas de ligação verdes quando concluído.
3. Conteúdo do passo (abaixo).

Estado: `rec = {step, req (nº AGHU), chk{id,mat,qtd,rec}, f{tipo,qtd,urg,urgM,proc,pat,orig,obs}, err{}, done (id do caso), code, msg, val, plantao}`.

### 3.2. Passo 1 — Ler etiqueta AGHU
**Card central** (ícone `scan-barcode` 40px azul, H2 "Ler etiqueta do AGHU"):
- Se AGHU indisponível: alerta amarelo "Recepção bloqueada: o AGHU está indisponível. As filas e os registros das demais etapas continuam funcionando." e o input fica **desabilitado**.
- **Input grande** (56px, fonte 18px 700, tabular): placeholder "Leia ou digite o nº da solicitação AGHU"; recebe foco automático; **Enter** dispara `recScan`.
  - Borda vermelha 2px quando há mensagem de erro.
  - Encontrou solicitação `Solicitado` → vai ao **passo 2** com `f.tipo = tipoSug` da solicitação e `f.qtd='1'`.
  - Solicitação já recebida → mensagem vermelha "A solicitação X já foi recebida como HP-00NN/26."
  - Não encontrada → "Nenhum registro encontrado para o código X. Confira a etiqueta ou digite o número. Material sem etiqueta do AGHU deve ser devolvido."
  - (Uma solicitação já **devolvida** cai nessa mensagem genérica — ver lacunas.)
- Botão destrutivo contornado: **"Material sem etiqueta do AGHU — registrar não conformidade"** → abre modal NC com contexto `semEtiqueta` (tipo pré-preenchido "Sem etiqueta do AGHU", exige unidade de origem).

**Card "Solicitações do AGHU aguardando recebimento"** (subtítulo: "Na rotina, a leitura da etiqueta abre a solicitação. A lista ajuda a demonstrar o fluxo."):
| Coluna | Conteúdo |
|---|---|
| Nº AGHU | `num` (negrito, tabular) |
| Paciente | nome (MAIÚSCULAS) |
| Exame | `tipoSug` (sigla, ex. HP) |
| Material | descrição (MAIÚSCULAS) |
| Origem | "Ambulatório (A)" / "Externo (E)" / "Internação (A)" / "Bloco cirúrgico (A)" |
| Solicitação | data/hora (alinhado à direita) |
| (ação) | botão "Ler etiqueta" (contorno verde; desabilitado se AGHU indisponível) → simula a leitura |
Estado vazio: "Nenhuma solicitação aguardando recebimento." Sem paginação/filtro.

### 3.3. Passo 2 — Conferir
Layout em 2 colunas (2fr / 1fr mín. 280px).

**Coluna esquerda — "Dados da solicitação"** + pílula azul "🔒 Origem: AGHU · somente leitura". Grid de campos somente leitura (estilo AGHU):
Nº da solicitação · Prontuário · Nome do paciente (2 col.) · Nascimento e idade (`dd/mm/aaaa · NN anos`) · Sexo · Origem (`Ambulatório (A)`/`Externo (E)`) · Unidade / clínica solicitante (2 col.) · Especialidade · Médico solicitante · Data da solicitação · Exame (2 col.) · Status no AGHU.
Abaixo, dois cards azuis em destaque: **Descrição do material** (ícone `test-tube`, texto 17px 700) e **Informações clínicas** (`stethoscope`).

**Coluna direita (sticky top 88px) — "Conferência"**: texto "Compare a amostra física e a requisição em papel com os dados do AGHU." Quatro checkboxes em card (todos obrigatórios):
1. Identificação confere com a requisição
2. Material corresponde à descrição
3. Quantidade de frascos confere
4. Recipiente íntegro e adequado

Botões:
- **Confirmar conferência** (primário, `circle-check`): se todos marcados → passo 3; senão erro inline: "Marque todos os itens da conferência. Se algo não confere, registre uma não conformidade."
- **Registrar não conformidade** (contorno vermelho) → modal NC com contexto `{req: nº}` (dados AGHU exibidos; origem vem da solicitação).
- **Ler outra etiqueta** (link verde) → `recReset` (volta ao passo 1, limpa tudo, foca input).

> O resultado dos checkboxes **não é persistido** no caso; o histórico só registra "Conferência sem divergências".

### 3.4. Passo 3 — Completar e confirmar entrada
Card único. Cabeçalho: "Completar e confirmar entrada" + "Solicitação AGHU **num** · NOME · MATERIAL"; à direita legenda "* Obrigatório".
Se validação ativa e há erros: **resumo** vermelho "Faltam N campos obrigatórios para confirmar" com lista de links que focam `#r-<campo>`.

| Campo | Tipo / controle | Obrigatório | Padrão | Regras / mensagem de erro |
|---|---|---|---|---|
| **Tipo de exame / fluxo** | radiogroup de cards: `HP` Histopatológico · `HD` Histopatológico dermatológico · `CG` Citologia geral / líquidos · `CV` Citopatológico oncótico · `CO` Congelação (intraoperatório) · `RI` Revisão de lâmina (IH **não** aparece) | Sim | `tipoSug` da solicitação AGHU; nota "Pré-selecionado a partir do exame do AGHU: <exame>" | "Selecione o tipo de exame." |
| **Quantidade de peças/frascos** (`r-qtd`) | `number`, min 1 | Sim | `1` | precisa ser ≥ 1 → "Informe 1 ou mais." |
| **Urgente?** (`r-urg`) | segmentado Sim/Não (Sim fica vermelho, Não verde) | Sim | **sem padrão** (vazio) | "Escolha Sim ou Não." |
| **Motivo da urgência** (`r-urgM`) | texto livre | Sim se Urgente=Sim (só aparece nesse caso) | — | "Descreva o motivo da urgência." |
| **Procedimento** (`r-proc`) | select ("Selecione" + lista `procedimentos`) | Sim | vazio | "Selecione o procedimento." |
| **Patologista designado** (`r-pat`) | select: Dr. Bruno Patologista / Dra. Helena Patologista | Sim **só para HP** (só aparece para HP) | vazio | "Selecione o patologista designado." |
| **Caso original para revisão** (`r-orig`) | texto, placeholder "Ex.: HP-0001/26" | Sim **só para RI** (só aparece para RI) | — | "Informe o nº do caso original." (sem validação de formato/existência) |
| **Observações** (`r-obs`) | textarea 3 linhas | Não | — | — |

Opções de **Procedimento**: Biópsia endoscópica; Biópsia por agulha grossa (core); Biópsia incisional; Biópsia excisional; Exérese de lesão de pele; Histerectomia; Colecistectomia; Apendicectomia; Tireoidectomia; Toracocentese; Punção aspirativa (PAAF); Coleta de citologia oncótica; Ressecção intraoperatória; Revisão de lâminas.

Faixa informativa cinza: "**Entrada:** <agora> (automático)" · "**Responsável:** <usuário> (automático)".

Botões (rodapé à direita):
- **Voltar à conferência** (secundário) → passo 2 (mantém marcações e campos).
- **Confirmar entrada** (primário, `circle-check`, dica "Ctrl+Enter") → `recConfirm`.

`recConfirm`:
1. Valida; havendo erros → ativa exibição de erros + toast warning "Faltam N campos obrigatórios para confirmar a entrada."
2. Gera **nº interno** com `nextId(tipo)`: `TT-NNNN/AA` — sequência **por tipo e por ano** (maior número existente do tipo no ano + 1, 4 dígitos; ano com 2 dígitos). Ex.: `HP-0015/26`, `CO-0002/26`, `CG-0006/26`.
3. Cria o caso com: `status='Recebido'`, `etapa = FLOWS[tipo][1]` (próxima etapa após a recepção), `entrada=etapaDesde=agora`, `urg`, `urgMotivo`, `qtd`, `procedimento`, `patologista` (**padrão "Dr. Bruno Patologista" quando não HP**), `residente='Dra. Carla Residente'` (fixo), `casoOriginal`, `obs`, cópia dos dados da solicitação em `sol` (com `statusAghu:'Solicitado'`).
4. Cria **N amostras-raiz** em `mat`: a 1ª com código = nº do caso; as seguintes `<id>-F2`, `<id>-F3`… (label "Amostra i · MATERIAL").
5. Histórico: "Entrada confirmada — Nº interno X gerado a partir da solicitação AGHU N. Conferência sem divergências." (setor Recepção, ícone `inbox`) e, se urgente, "Marcado como URGENTE — <motivo>".
6. Solicitação AGHU muda para `status='Recebida'` (sai da lista pendente; badge do menu decrementa) e guarda `caseId`.
7. Auditoria `Negócio clínico / Entrada confirmada / Caso X / antes '—' / depois 'Solicitação AGHU N'`.
8. Vai ao passo 4; toast success "Entrada confirmada. Caso X criado."

### 3.5. Passo 4 — Etiquetas e ficha (confirmação)
Card centralizado:
- Círculo verde com `circle-check`; "Entrada confirmada · nº interno gerado"; **nº do caso** em 28px 800 + botão copiar (toast "Nº X copiado.").
- Badge **URGENTE** se aplicável.
- "Encaminhado para: **<etapa>**" (Macroscopia / Processamento técnico / Congelação / Microscopia).
- **Somente CO (congelação)**: alerta vermelho (ícone `snowflake`) "Congelação: acionar equipe de plantão — A cirurgia está em andamento. Avise o patologista de plantão agora." + botão **"Acionar equipe de plantão"** → registra no histórico "Equipe de plantão de congelação acionada — Patologista de plantão: Dr. Bruno Patologista." e o botão vira "Equipe acionada" (idempotente); toast "Equipe de plantão de congelação acionada."
- Lembrete amarelo (`bell-ring`): "**Lembrete:** registrar o recebimento no AGHU (solicitação N)." (não há integração de escrita no AGHU).
- Botões: **Imprimir etiqueta(s)** (abre pré-visualização de etiquetas das amostras-raiz), **Imprimir ficha de trabalho** (A4), **Receber próxima amostra** (primário → `recReset`).
- Link "Abrir detalhe do caso" → tela do caso.

### 3.6. Modal "Não conformidade e devolução" (usado na recepção e nas etapas)
Gatilhos: (a) botão "Material sem etiqueta…" no passo 1 (`ctx.semEtiqueta`); (b) "Registrar não conformidade" no passo 2 (`ctx.req`); (c) "Não conformidade" no detalhe do caso ou na tela de etapa (`ctx.caseId`).
Modal 720px, ícone `circle-alert` vermelho, título "Não conformidade e devolução", indicador "Passo 1 de 2"/"Passo 2 de 2".
Faixa de contexto (cinza): **Setor** (Recepção ou rótulo do perfil), **Etapa** ("Recepção (leitura)" sem etiqueta / "Recepção (conferência)" com solicitação / rótulo da etapa atual do caso), **Caso** ("—" se ainda não existe), **Data/hora**, **Profissional**.

**Passo 1**
- Cartões AGHU (azuis): SOLICITAÇÃO (nº ou "Sem etiqueta do AGHU"), EXAME, e quando há solicitação: ORIGEM ("Unidade (A/E)"), MÉDICO / ESPECIALIDADE.
- **Unidade de origem** * (select, só quando não há solicitação/caso) — opções `unidades`: Ambulatório de Gastroenterologia, de Mastologia, de Dermatologia, de Ginecologia, de Urologia, de Endocrinologia; Bloco Cirúrgico; Enfermaria de Cirurgia Geral, de Clínica Médica, de Oncologia, de Pneumologia; Paciente externo. Erro: "Selecione a unidade de origem."
- **Tipo de inconformidade** * (select) — `ncTipos`: Sem etiqueta do AGHU; Identificação divergente; Quantidade divergente; Material inadequado / insuficiente; Recipiente danificado / vazamento; Sem fixador / fixação inadequada; Requisição incompleta; Outro. Erro: "Selecione o tipo de inconformidade."
- **Nº CMCE (opcional)** (texto).
- **Detalhamento** * (textarea, placeholder "O que foi encontrado na amostra?"). Erro: "Descreva o que foi encontrado."
- Botões: **Voltar** (fecha) · **Registrar não conformidade** (→ passo 2 se válido).

**Passo 2**
- Resumo vermelho: "**<tipo>** — <detalhamento>".
- **Quem devolveu** (somente leitura = usuário atual).
- **Quem recebeu na unidade de origem** * (texto). Erro: "Informe quem recebeu o material na origem."
- **Nova amostra solicitada?** * (segmentado Sim/Não, sem padrão). Erro: "Escolha Sim ou Não."
- **Resolvido?** (select; padrão "Pendente"; opções Pendente / Nova amostra recebida / Encerrado sem reenvio).
- Botões: **Voltar** (passo 1) · **Registrar devolução** (vermelho, ícone `undo-2`).

`ncSave` — resultado:
- Registro NC: `{tipo, det, setor, etapa, t, por, cmce, origem (unidade da solicitação ou selecionada), recebeu, nova, acomp, caso}`.
- **Com caso**: adiciona em `caso.ncs`, `status='Devolvido'` (caso sai das filas ativas e fica bloqueado), histórico "Não conformidade registrada" + "Material devolvido à origem — Recebido por X. Nova amostra solicitada: Sim/Não."
- **Sem caso (recepção)**: adiciona em `db.rejeicoes` (topo); com solicitação → solicitação AGHU `status='Devolvida'` e `rec.aghu = nº`.
- Auditoria `Negócio clínico / Não conformidade e devolução`.
- Toast "Não conformidade e devolução registradas. O material saiu das filas ativas."
- Na recepção volta ao passo 1 (`recReset`); na tela de etapa volta à fila.
- Observação: **não existe NC sem devolução** — o fluxo sempre termina em devolução.

### 3.7. Impressão (modal `print`)
Pré-visualização em tela cheia: barra com ícone impressora, título, "Pré-visualização em preto e branco", **Fechar**, **Imprimir** (`window.print()` + histórico "Etiquetas impressas"/"Ficha de trabalho impressa"/"Laudo em PDF gerado").
- **Etiquetas** (título "Etiquetas · N itens"): cartões **50 mm × 25 mm** com código de barras (18×19 mm), **código** (9pt 800), **tipo do item** ("Amostra", "Bloco A", "Lâmina A-01", "Lâminas diretas", "Cell-block"), **iniciais do paciente** (ex.: "S.A.L." — ignora DA/DE/DO/DAS/DOS/E) e **data** (dd/mm/aaaa). Na recepção imprime as amostras-raiz.
- **Ficha de trabalho (A4)**: cabeçalho "Hospital das Clínicas da UFPE · Serviço de Anatomia Patológica", "Ficha de trabalho", tipo; nº do caso grande + código de barras. Tabela: Paciente; Prontuário | Solicitação AGHU; Nascimento (idade) | Sexo; Unidade | Médico; Material | Procedimento; Entrada | Urgente ("URGENTE — motivo" ou "Não"). Bloco "Informações clínicas". Tabela "Acompanhamento físico por setor" (uma linha por etapa do fluxo do tipo; colunas Setor, Data/hora, Responsável, Visto — em branco para preenchimento manual). "Anotações" (caixa). Rodapé "Página 1 de 1" · "Emitido em …".
- **Laudo (A4)**: placeholder de cabeçalho institucional, nº + barcode, dados do paciente, Informações clínicas, Macroscopia, Microscopia, IHQ (se houver), Conclusão, assinaturas (patologista, residente).

### 3.8. Regras de negócio da recepção (resumo)
- Só recebe material com **etiqueta AGHU** e solicitação `Solicitado`; sem etiqueta → NC/devolução obrigatória.
- AGHU indisponível bloqueia a recepção (input e botões desabilitados), mas não as demais etapas.
- Conferência com 4 itens obrigatórios; qualquer divergência → NC.
- Tipo de exame sugerido pelo AGHU, editável. Fluxo determinado pelo tipo (`FLOWS`):
  - HP: recepção → macroscopia → processamento → microscopia → arquivo
  - HD, CG, CV: recepção → processamento → microscopia → arquivo
  - CO: recepção → congelação → microscopia → arquivo
  - RI: recepção → microscopia → arquivo
  - IH (só via solicitação complementar): ihq → microscopia
- Urgência exige motivo; urgente aparece destacado em todas as listas (ordenado primeiro).
- HP exige patologista designado; RI exige nº do caso original.
- Prazo padrão da etapa recepção: 1 dia (configurável).
- Após confirmação o caso fica `Recebido` até ser **lido** no setor seguinte (aí muda para "Em macroscopia" etc. e registra "Chegada registrada na etapa X").
- CO dispara alerta de plantão; congelação tem cronômetro de referência de 40 min (`prazos.etapa.congelacao = 0.028` dia ≈ 40 min).

---

## 4. Consulta de casos (DETALHADO)

**Tela:** `screen='consulta'` · menu "Consulta de casos" · **H1 "Consulta e pesquisa de casos"** · subtítulo "Todos os casos, inclusive devolvidos, cancelados e arquivados." · sem limite de largura.
**Atores:** todos os perfis (gestor vê dados de paciente ocultos).
**Objetivo:** localizar qualquer caso e abrir seu detalhe.

### 4.1. Layout
- Cabeçalho com H1/subtítulo e botão **Exportar** (contorno verde, ícone `download`) à direita.
- Card com:
  1. **Barra de filtros** (flex-wrap):
     - **Buscar** (texto, flex 280px). Placeholder: "Nº interno, nº AGHU, prontuário ou nome" (gestor: "Nº interno ou nº AGHU"). Busca *contains*, case-insensitive, em `id`, `sol.num` (+ `pront` e `nome` exceto gestor). Filtra a cada digitação.
     - **Status** (select, "Todos" + 13 status — ver §6.3).
     - **Tipo** (select, "Todos" + HP, HD, CG, CV, CO, RI, IH).
     - **Patologista** (select, "Todos" / Dr. Bruno Patologista / Dra. Helena Patologista).
     - **Período** (select: Qualquer data / Últimos 7 / 30 / 90 dias — pela data de entrada).
     - Toggle **Somente urgentes** (ícone `triangle-alert`; ativo = fundo `#fbe3e4`, borda/texto vermelhos).
     - Qualquer mudança de filtro volta à página 1.
  2. **Chips de filtros ativos** (se houver): "Busca: X", "<status>", "Tipo HP", "Somente urgentes", "<patologista>", "Últimos N dias", cada um com ✕; botão "Limpar filtros".
  3. **Skeleton** (5 barras) durante 450ms ao entrar.
  4. **Tabela** (rolagem horizontal):
     | Coluna | Conteúdo |
     |---|---|
     | Nº interno | link azul sublinhado + badge URGENTE + indicadores (Rascunho / Estagnado / Retrabalho) |
     | Tipo | sigla |
     | Paciente | nome + "Pront. NNNNNNN" (gestor: "Oculto"/"oculto") |
     | Nº AGHU | nº da solicitação (gestor "—"; IHQ derivada fica vazio) |
     | Material | descrição |
     | Status | badge de status (cor/ícone por status) |
     | Entrada ↓ | data/hora (ícone de seta fixo; não é ordenável por clique) |
     | Patologista | nome ou "—" |
     Linha inteira clicável (hover cinza) → `openCase(id)`; linhas urgentes com barra vermelha 4px à esquerda.
     **Ordenação fixa:** urgentes primeiro, depois entrada mais recente.
  5. **Estado vazio**: ícone `search-x` 48px, "Nenhum caso encontrado", "Revise a busca ou limpe os filtros."
  6. **Rodapé de paginação**: "Mostrando 1–10 de 22" (ou "Nenhum resultado") · botões **Anterior** / "Página X de Y" / **Próxima** (desabilitados nos limites). **10 itens por página.**

### 4.2. Exportar
Gera `consulta-casos.csv` (UTF-8 com BOM, separador `;`, valores entre aspas) com **todos os resultados filtrados** (não só a página). Colunas: Nº interno, Tipo, Paciente, Prontuário, AGHU, Material, Status, Entrada, Patologista (gestor: sem Paciente/Prontuário/AGHU). Toast "Arquivo consulta-casos.csv exportado."

### 4.3. Detalhe do caso (destino da consulta) — `screen='caso'`
- **Cabeçalho**: nº do caso (grande) + copiar; badge de status; URGENTE (tooltip com motivo); indicadores. Linha de metadados: "HP · Histopatológico", "NOME · Pront. N" (gestor: "Paciente: oculto para o perfil Gestor"), "Material: X", "Patologista: X", badge de prazo "N de P dias desde a entrada" (prazo total por tipo).
- **Ações** (conforme perfil/estado): **Cancelar caso** (gestor/admin, caso ativo), **Não conformidade** (perfis operacionais incluindo Recepção, caso ativo e sem laudo concluído), **Imprimir ▾** (Etiquetas | Ficha de trabalho | Laudo em PDF se concluído), **Solicitação complementar** (residente/patologista em microscopia, exceto CV), botão da etapa do perfil (ex.: "Registrar macroscopia", "Revisar e aprovar", "Registrar laudo", "Registrar arquivamento").
- **Faixa de bloqueio** (cadeado) quando Devolvido/Cancelado/Arquivado/laudo concluído: "Caso cancelado — fora das filas ativas. Consulta somente leitura." / "Caso devolvido por não conformidade — fora das filas ativas." / "Caso arquivado. Histórico completo disponível." / "Laudo concluído — o caso não pode mais ser alterado."
- **Stepper do fluxo** (etapas do tipo; IHQ inserida antes da microscopia se houver solicitação de IHQ): concluídas ✓ verde; atual azul pulsando com status abaixo; parada (Devolvido/Cancelado) com ✕ cinza; marcador "↺ N" de retornos por etapa.
- **12 abas**: Resumo · Solicitação AGHU · Recepção · Macroscopia · Processamento · IHQ · Microscopia · Laudo · Arquivo · Materiais · Não conformidades · Histórico.
  - *Resumo*: Tipo, Material (AGHU), Entrada, Etapa atual, Tempo na etapa, Prazo total do laudo, Patologista designado, Residente, Retornos, Procedimento ou Caso de origem; Informações clínicas (AGHU); cards de cada solicitação complementar. Coluna lateral: **Pendências** (rascunhos, aprovação pendente, IHQ externa, solicitação complementar aberta, "Aguardando leitura do código na etapa X", "Aguardando material complementar pela recepção", "Tempo na etapa acima do padrão", "Lembrete: liberar laudo no AGHU") ou "Nada pendente para este caso avançar."; **Últimas movimentações** (5) + "Ver histórico completo".
  - *Solicitação AGHU* (badge "Origem: AGHU", campos azuis com 🔒): nº, prontuário, nome, nascimento/idade, sexo, origem, unidade, especialidade, médico, data, exame, status no AGHU, descrição do material, informações clínicas.
  - *Recepção*: Entrada, Responsável, Tipo de exame, Quantidade de peças/frascos, Urgente, Motivo da urgência, Procedimento, Patologista designado, Caso original (revisão), Observações. (IH: "IHQ aberta a partir de solicitação complementar do caso X.")
  - *Materiais*: árvore Amostra → Bloco → Lâmina (ícones `test-tube`/`box`/`rectangle-horizontal`), código clicável (copia), contagem, origem (Rotina ou "Solicitação complementar (…)"), data · responsável, botão **reimprimir etiqueta** por item; total "N amostras · N blocos · N lâminas".
  - *Não conformidades*: cards com Setor, Etapa, Data/hora, Profissional, Nº CMCE, Recebido na origem por, Nova amostra solicitada?, Acompanhamento, Detalhamento; cancelamento (motivo, por, quando); vazio "Nenhuma não conformidade registrada neste caso."
  - *Histórico*: linha do tempo imutável ("Registro imutável"), ícone por evento, ação, setor, data · usuário, `<details>` com detalhes.

---

## 5. Rejeições e devoluções (DETALHADO)

**Tela:** `screen='devolucoes'` · menu "Rejeições e devoluções" (grupo Acompanhamento, ícone `undo-2`) · H1 "Rejeições e devoluções" · subtítulo "Amostras devolvidas por não conformidade, com acompanhamento da resolução."
**Atores:** **todos os perfis** veem e podem alterar o acompanhamento (não há restrição de edição por perfil).
**Objetivo:** listar todas as NCs que geraram devolução — tanto **rejeições na recepção** (sem caso criado, `db.rejeicoes`) quanto **devoluções de casos** já criados (`caso.ncs`) — e acompanhar a resolução.

### 5.1. Layout
Card único:
1. **Filtros** (flex-wrap):
   - **Período**: Qualquer data / Últimos 7 dias / Últimos 30 dias (pela data da NC).
   - **Tipo**: Todos + `ncTipos` (8 tipos).
   - **Origem**: Todas + lista dinâmica das origens presentes nos registros.
   - **Etapa identificada**: Todas / Recepção / Macroscopia / Processamento técnico / Microscopia (filtro por *prefixo*, então "Recepção" pega "Recepção (conferência)" e "Recepção (leitura)").
   - Contador à direita: "N registros".
   - Sem chips, sem busca textual, sem exportação, **sem paginação**.
2. **Tabela** (ordenada por data desc.):
   | Coluna | Conteúdo |
   |---|---|
   | Data/hora | `dd/mm/aaaa hh:mm` |
   | Tipo | tipo em negrito + detalhamento (13px cinza) |
   | Origem | unidade de origem |
   | Etapa | etapa em que foi identificada |
   | Caso | botão-link com nº do caso (abre detalhe); para rejeição na recepção: "AGHU 4830112" (desabilitado) ou "—" |
   | Devolvido por / recebido por | profissional SAP / nome de quem recebeu na origem |
   | Nova amostra | Sim / Não |
   | Resolvido? | **select inline** Pendente / Nova amostra recebida / Encerrado sem reenvio |
3. Estado vazio: "Nenhuma devolução no período e filtros selecionados."

### 5.2. Ação: alterar "Resolvido?"
Muda `acomp` do registro, grava auditoria `Negócio clínico / Acompanhamento de devolução atualizado / <caso> / antes / depois`, toast "Acompanhamento atualizado." Não altera o status do caso nem vincula nova amostra a novo caso.

### 5.3. Dados de exemplo exibidos (seed)
| Data | Tipo | Detalhe | Origem | Etapa | Caso | Por / Recebeu | Nova | Resolvido |
|---|---|---|---|---|---|---|---|---|
| há 3 dias | Sem etiqueta do AGHU | Frasco com biópsia de pele sem etiqueta do AGHU, apenas nome manuscrito. | Ambulatório de Dermatologia | Recepção | — | Ana Lúcia Recepção / Téc. enf. Sandra Lopes | Sim | Nova amostra recebida |
| há ~6 dias | Identificação divergente | Nome no frasco difere do nome na requisição (sobrenome trocado). | Ambulatório de Endocrinologia | Recepção | CG-0005/26 | Ana Lúcia Recepção / Téc. enf. Rogério Silva | Sim | Nova amostra recebida |
| há ~9 dias | Sem fixador / fixação inadequada | Peça recebida sem formol, com sinais de autólise. | Bloco Cirúrgico | Macroscopia | HP-0014/26 | Marcos Técnico Macroscopia / Enf. Joana Ribeiro (Bloco Cirúrgico) | Sim | Pendente |

### 5.4. Integrações
- Origem dos registros: modal NC (recepção passo 1/2 ou qualquer etapa/detalhe do caso).
- Rejeição na recepção não cria caso → não aparece na Consulta; a solicitação AGHU fica `Devolvida` e some da lista pendente.
- Devolução de caso → caso `Devolvido` aparece na Consulta (filtrável por status "Devolvido") e no detalhe com aba "Não conformidades".
- Indicadores (KPI) têm "Taxa de não conformidades", NC por tipo/etapa/origem (dados estáticos mockados, não calculados).
- Cancelamento (gestor/admin) **não** aparece nesta tela (só no detalhe/consulta como status "Cancelado").

---

## 6. Modelo de dados mockados e status

### 6.1. Entidades (`AP.seed(now)`)
```ts
db = { users, cases, aghu, rejeicoes, audit, prazos, lists, masks, aghuDown:false }
```

**Solicitação AGHU (`aghu[]`)** — 4 pendentes:
```js
{ num:'4830112', nome:'SEVERINA ALVES DE LIMA', pront:'1170034', nasc:'1968-02-14', sexo:'Feminino',
  origem:'Ambulatório'|'Externo'|'Bloco cirúrgico'|'Internação',
  unidade:'Ambulatório de Mastologia', esp:'Mastologia', med:'Dra. Renata Queiroz',
  data:<timestamp>, exame:'HP – Exame anatomopatológico', tipoSug:'HP',
  material:'NÓDULO DE MAMA', info:'Nódulo palpável em QSE…', statusAghu:'Solicitado',
  status:'Solicitado'|'Recebida'|'Devolvida', caseId? }
```
| num | Paciente | tipoSug | Material | Origem / unidade |
|---|---|---|---|---|
| 4830112 | SEVERINA ALVES DE LIMA | HP | NÓDULO DE MAMA | Ambulatório / Ambulatório de Mastologia |
| 4830245 | CLAUDIONOR XAVIER NETO | HD | PELE – LESÃO DORSO | Externo / Paciente externo – UBS Várzea |
| 4830301 | JULIANA MEDEIROS PORTO | CO | NÓDULO DE TIREOIDE | Bloco cirúrgico / Bloco Cirúrgico – Sala 4 |
| 4830377 | SEBASTIÃO RIBEIRO FILHO | CG | LÍQUIDO PLEURAL | Internação / Enfermaria de Pneumologia |

Formatos: nº AGHU 7 dígitos; prontuário 7 dígitos (pode começar com 0); nascimento ISO `AAAA-MM-DD`; nomes e materiais em MAIÚSCULAS; origem exibida com sufixo "(E)" para Externo e "(A)" para os demais.

**Caso (`cases[]`)**:
```js
{ id:'HP-0004/26', tipo:'HP', sol:{...cópia AGHU, statusAghu}, material, procedimento,
  etapa:'recepcao'|'macroscopia'|'processamento'|'congelacao'|'ihq'|'microscopia'|'arquivo'|'fim',
  status:<ver 6.3>, entrada, etapaDesde, urg, urgMotivo, qtd, patologista, residente, casoOriginal, obs,
  origem?:'HP-0006/26' (para IH), mat:[ItemMaterial], hist:[Evento], ncs:[NC], comps:[SolicComplementar],
  drafts:{[etapa]:{...campos, missing:[rótulos], savedAt}}, arr:{[etapa]:true /*chegada lida*/},
  macro, proc, cong, micro{parecer,por,em}, triagem, ihq{aghuIhq,blocos,anticorpos[{nome,interno}],lab,patLaudo,ext}, 
  aprovado, aprovadoPor, laudo{texto,pat,res,em,concluido}, arquivo, saidas[], cancel{motivo,por,t},
  retornos, aguardaMaterial, devolvidoObs }
```
**Item de material** (árvore): `{code, tipo:'Amostra'|'Bloco'|'Lâmina', label, em, por, origem:'Rotina'|'Solicitação complementar (…)', children[]}`.
Códigos: amostra `HP-0004/26` (extras `-F2`, `-F3`); bloco `HP-0004/26-A` (letras A, B…; citologia `-L` lâminas diretas; `-CB` cell-block); lâmina `HP-0004/26-A-01` (2 dígitos).

**Evento de histórico**: `{t, user, setor, acao, det, icon}`.
**NC/devolução**: `{tipo, det, setor, etapa, t, por, cmce, origem, recebeu, nova:'Sim'|'Não', acomp:'Pendente'|'Nova amostra recebida'|'Encerrado sem reenvio', caso, aghu?}`.
**Auditoria**: `{t, user, ip:'10.32.14.x', cat:'Segurança'|'Negócio clínico'|'Configuração', acao, rec, antes, depois}`.
**Usuário**: `{login, nome, lot, perfis[], email:login@ebserh.gov.br, ativo}` (13 usuários; `sandra.moura` inativo; `carla.residente` tem residente+macroscopia; `helena.patologista` patologista+gestor).
**Prazos**: etapa (dias) `recepcao 1, macroscopia 2, processamento 2, congelacao 0.028 (~40 min), ihq 5, microscopia 4, aprovacao 2, arquivo 3`; total do laudo por tipo `HP 10, HD 7, CG 5, CV 15, CO 1, RI 7, IH 10`.

### 6.2. Casos de exemplo (22)
| Nº | Paciente | Material | Status | Observação |
|---|---|---|---|---|
| HP-0001/26 | MARIA JOSÉ DA SILVA SANTOS | BIÓPSIA GÁSTRICA | Arquivado | completo |
| HP-0002/26 | JOÃO BATISTA FERREIRA LIMA | VESÍCULA BILIAR | Laudo concluído | aguarda arquivo |
| HP-0003/26 | ANTÔNIA PEREIRA DE SOUZA | ÚTERO | Em arquivamento | rascunho de arquivo |
| HP-0004/26 | JOSEFA MARIA DO NASCIMENTO | NÓDULO DE MAMA | Aguardando aprovação | URGENTE "Programação cirúrgica oncológica" |
| HP-0005/26 | FRANCISCO DAS CHAGAS OLIVEIRA | BX DE PRÓSTATA | Em microscopia | 6 cassetes |
| HP-0006/26 | ROSÂNGELA CAVALCANTI MOURA | NÓDULO DE MAMA | IHQ externa – aguardando resultado | 2 retornos (recorte + IHQ) |
| IH-0002/26 | (idem) | BLOCO B – HP-0006/26 | IHQ externa – aguardando resultado | HER2 no AC Camargo há 12 dias |
| HP-0009/26 | PEDRO HENRIQUE BEZERRA | LINFONODO CERVICAL | Em IHQ | painel linfoide |
| IH-0003/26 | (idem) | BLOCO A – HP-0009/26 | Em IHQ | |
| HP-0010/26 | LUCIANA ARAÚJO TAVARES | ÚTERO | Em macroscopia | rascunho incompleto |
| HP-0011/26 | JOSÉ CARLOS MONTEIRO | BIÓPSIA GÁSTRICA | Em macroscopia | URGENTE |
| HP-0012/26 | FERNANDA LIRA BARBOSA | APÊNDICE CECAL | Em processamento técnico | estagnado (8 dias) |
| HP-0013/26 | EDILEUZA GOMES DA ROCHA | NÓDULO DE TIREOIDE | **Recebido** | aguardando leitura na macroscopia |
| HP-0014/26 | CÍCERO RAMOS DE ALBUQUERQUE | INTESTINO GROSSO – COLECTOMIA | **Devolvido** | NC sem fixador |
| HD-0001/26 | MARLENE VIEIRA DUARTE | PELE – LESÃO FACE | Aguardando aprovação | Dra. Helena |
| HD-0002/26 | (idem) | PELE – LESÃO FACE | **Cancelado** | duplicidade no AGHU |
| HD-0003/26 | RAIMUNDO NONATO COSTA | PELE – LESÃO DORSO | Em processamento técnico | sem chegada registrada |
| CG-0004/26 | TEREZINHA DE JESUS PAIVA | LÍQUIDO PLEURAL | Em processamento técnico | URGENTE |
| CG-0005/26 | GABRIELA FARIAS MELO | PAAF DE TIREOIDE | **Devolvido** | NC na recepção (identificação) |
| CV-0006/26 | VALDETE CORREIA BRAGA | COLO UTERINO | Aguardando aprovação | triagem alterada |
| CV-0007/26 | LÚCIA HELENA PIMENTEL | COLO UTERINO | Em microscopia | |
| CO-0001/26 | ANTÔNIO MARCOS SIQUEIRA | NÓDULO PULMONAR – CONGELAÇÃO | Em congelação | 21 min desde a entrada |
| RI-0002/26 | MARIA JOSÉ DA SILVA SANTOS | LÂMINAS – REVISÃO DE HP-0001/26 | Em microscopia | casoOriginal HP-0001/26 |

Médicos solicitantes fictícios: Dr. Ricardo Menezes, Dr. Paulo Arruda, Dra. Simone Vasconcelos, Dra. Renata Queiroz, Dr. Henrique Cabral, Dr. Lucas Tenório, Dra. Patrícia Lemos, Dr. Augusto Pessoa, Dr. Sérgio Cunha, Dra. Beatriz Holanda, Dr. Marcelo Diniz, Dra. Camila Rocha, Dr. Eduardo Falcão, Dr. Otávio Brandão, Dr. Felipe Andrade.

### 6.3. Status do caso (`AP.SS` → badge)
| Status (exato) | Categoria/cor | Ícone | Spec (04-modelo-dados) |
|---|---|---|---|
| Recebido | info (azul) | inbox | RECEBIDO |
| Em macroscopia | info | scissors | EM_MACROSCOPIA |
| Em congelação | info | snowflake | EM_CONGELACAO |
| Em processamento técnico | info | flask-conical | EM_PROCESSAMENTO |
| Em IHQ | info | test-tubes | EM_IHQ |
| IHQ externa – aguardando resultado | warn (amarelo) | clock | IHQ_AGUARDANDO_EXTERNO |
| Em microscopia | info | microscope | EM_MICROSCOPIA |
| Aguardando aprovação | warn | clock | AGUARDANDO_APROVACAO |
| Laudo concluído | ok (verde) | circle-check | LAUDO_CONCLUIDO |
| Em arquivamento | info | archive | EM_ARQUIVAMENTO |
| Arquivado | ok | circle-check | ARQUIVADO |
| Devolvido | neutral (cinza) | undo-2 | DEVOLVIDO |
| Cancelado | neutral | circle-x | CANCELADO |
Os 13 status batem 1:1 com os sugeridos na especificação.

### 6.4. Transições (quem dispara)
- **Recepção confirma entrada** → `Recebido` (etapa = próxima do fluxo).
- **Leitura do código no setor** (dono da etapa) → `Em <etapa>` (registra chegada).
- **Macroscopia conclui** → etapa processamento (status muda ao ser lido) — gera blocos.
- **Processamento conclui** → etapa microscopia — gera lâminas.
- **Congelação registra diagnóstico intraoperatório** → microscopia.
- **Residente envia parecer** / **Citotécnico envia triagem** → `Aguardando aprovação`.
- **Patologista aprova** → `Em microscopia` com `aprovado=true` → **Concluir caso** → `Laudo concluído` (etapa arquivo).
- **Patologista devolve ao residente** → `Em microscopia` (com observações).
- **Solicitação complementar** (residente/patologista) → volta para processamento/macroscopia, ou abre caso IH (`Em IHQ`), ou marca aguardando material da recepção.
- **IHQ envia externo** → `IHQ externa – aguardando resultado` (também no caso de origem); **recebe resultado** → `Em IHQ`; **conclui IHQ** → IH `Laudo concluído`, origem volta à microscopia.
- **Arquivo lê** (`Laudo concluído`) → `Em arquivamento`; **registra arquivamento** (confirmação) → `Arquivado`.
- **Qualquer setor operacional** registra NC+devolução → `Devolvido` (bloqueado).
- **Gestor/Admin** cancela (2 passos, motivo obrigatório) → `Cancelado`.
Bloqueados (`locked`): Devolvido, Cancelado, Arquivado.

### 6.5. Indicadores derivados
- **Rascunho**: algum `drafts[etapa].missing` não vazio.
- **Estagnado**: tempo na etapa > prazo da etapa.
- **Retrabalho**: solicitação complementar `Aberta`.
- Status da solicitação AGHU: `Solicitado` → `Recebida` | `Devolvida`.

---

## 7. Demais telas (resumo)

| Tela | Perfis | Propósito / conteúdo | Relação com a recepção |
|---|---|---|---|
| **Minha fila** (`fila`) | operacionais | Título por perfil (ex.: "Fila da macroscopia", "Minha fila de microscopia", "Aguardando minha aprovação", "Fila do arquivo"). 4 cards-filtro (Aguardando no meu setor, Urgentes, Rascunhos, Estagnados). Filtros: tipo, período (24h/7/30 dias), Somente urgentes, Somente rascunhos. Tabela: Nº, Tipo, Material, Status da etapa (Aguardando/Em andamento/Rascunho/Aguardando aprovação/Laudo a registrar), Entrada na etapa, Tempo na etapa (badge prazo), Ação (Iniciar etapa / Continuar / Continuar rascunho / Revisar / Registrar laudo). Ordem: urgentes, depois mais antigos. IHQ tem quadro extra "IHQ externas pendentes". | Casos recém-recebidos aparecem como "Aguardando" na fila do setor seguinte. |
| **Etapa** (`etapa`) | dono da etapa | Formulários: **Macroscopia** (tipo de material, máscara de texto, editor rico da descrição, cassetes com nº fragmentos + descrição, sobra em fixador, coloração especial, rota Histotécnico/Manual, imprimir etiquetas de cassetes, copiar para AGHU); **Processamento** (líquido/centrifugação/cell-block p/ CG, rota, 5 subetapas, confirmação de blocos e nº de lâminas/coloração); **Congelação** (cronômetro 40 min, patologista, análise macro, lâminas no criostato, diagnóstico, hora de comunicação); **IHQ** (nº AGHU da IHQ, blocos, painel até 25 anticorpos, envio/recebimento externo, PDF, patologista do laudo); **Microscopia** (parecer com máscara, "Diagnóstico fechado?"); **Triagem citotécnica** (adequabilidade, resultado); **Aprovação/laudo** (aprovar, devolver ao residente, texto final, concluir); **Arquivo** (Siscan, data, itens arquivados, local). Barra: Salvar rascunho (Ctrl+S), NC, Solicitação complementar, botão principal (Ctrl+Enter). Validação com resumo de erros; conclusão incompleta vira rascunho. | Herda dados da recepção (urgência, procedimento, patologista). NC pode ser aberta de qualquer etapa. |
| **Detalhe do caso** (`caso`) | todos | Ver §4.3. | Aba Recepção mostra o registro da entrada. |
| **Pendências e alertas** (`pendencias`) | todos | Grupos: Alertas de estagnação; Rascunhos com campos faltantes; Aprovações paradas; IHQ externa sem resultado; Etapas sem registro (encaminhado há > 12 h sem leitura). Legenda amarelo/vermelho. | Casos `Recebido` não lidos no setor seguinte entram em "Etapas sem registro". |
| **Painel de processos** (`kanban`) | todos | "Painel de processos em andamento · N casos ativos · sem dados identificáveis de pacientes". Colunas: Recepção (status Recebido), Macroscopia, Congelação, Processamento, IHQ, Microscopia, Aguardando aprovação, Arquivo; contagem e média de tempo; cards com nº, tipo, URGENTE, prazo, total, indicadores. "Atualizado há N s · atualização automática a cada 30 s". | Coluna **Recepção** = casos `Recebido` aguardando leitura no próximo setor. |
| **Indicadores** (`kpis`) | gestor, admin, patologista | Dados agregados estáticos (`AP.KPI`, escalados por período 30/90/365): cards Taxa de retrabalho 18,4%, Laudos no prazo 76,2%, TAT 8,6 dias, Taxa de NC 3,1%, Completude 91,5% (com deltas); barras por etapa, TAT mensal, retrabalho por tipo/setor, prazo por tipo/patologista (meta 75%), NC por tipo/etapa/origem, completude. Filtros período/setor/etapa/tipo (só período tem efeito). Exportar `indicadores-sap.csv`. | NC por etapa "Recepção 6, Macroscopia 2"; NC por origem. |
| **Configurações** (`config`) | admin (5 abas) / patologista (só Máscaras) | **Usuários e perfis** (busca; tabela Nome, Login/e-mail, Lotação, Perfis, Situação; Editar perfis; Ativar/Desativar; **Novo usuário** → login de rede + "Consultar AD" (mock: joao.pereira, mariana.lins, tiago.alves) preenche nome/e-mail/lotação; perfis em toggles; salvar exige AD consultado e ≥1 perfil). **Máscaras de texto** (nome, material, etapa, texto, ativa). **Listas padronizadas** (materiais, procedimentos, tipos de inconformidade, anticorpos, laboratórios externos, colorações, origens/unidades — só adicionar). **Prazos padrão** (por etapa e total por tipo). **Protótipo** (toggle AGHU disponível/indisponível; restaurar dados). Tudo auditado. | Listas de procedimentos, tipos de NC e unidades alimentam a recepção/NC; prazo da recepção. |
| **Auditoria** (`auditoria`) | admin | "Somente leitura. Registros não podem ser alterados nem apagados." Filtro categoria (Segurança / Negócio clínico / Configuração). Tabela: Data/hora, Usuário, IP, Categoria (badge colorido), Ação, Recurso, Antes × depois ("Comparar"). | Entrada confirmada e NC/devolução geram registros "Negócio clínico". |

Modais restantes: **Solicitação complementar** (tipo: Recorte, Coloração especial, Recoloração, Nova laminação, Painel/ampliação IHQ, Revisão da peça, Material complementar → setor de destino automático; blocos; anticorpos; detalhamento; justificativa obrigatória); **Cancelar caso** (2 passos); **Devolver parecer ao residente**; **Saída/retirada de material** (arquivo: quem retirou, destino, itens, devolução prevista); **Confirmação genérica**.

---

## 8. Lacunas, inconsistências e dúvidas a validar com os usuários

### Recepção
1. **Conferência não é persistida**: os 4 checkboxes não são salvos no caso (spec prevê tabela `conferencia_recebimento` com `resultado` ACEITA/REJEITADA/PENDENTE e os 4 booleanos + observação). O histórico só diz "Conferência sem divergências".
2. **NC sempre gera devolução**: o modal não permite registrar uma não conformidade sem devolver (spec: `nao_conformidade 0..1 devolucao`, status ABERTA/EM_TRATAMENTO/RESOLVIDA/CANCELADA). Confirmar se existe NC "corrigível" sem devolução (ex.: requisição incompleta resolvida por telefone).
3. **"Resolvido?" vs status da spec**: protótipo usa Pendente / Nova amostra recebida / Encerrado sem reenvio; spec usa `AGUARDANDO_NOVA_AMOSTRA`, `NOVA_AMOSTRA_RECEBIDA`, `ENCERRADA` (e campo `novo_caso_id`). Não há vínculo da nova amostra ao novo caso.
4. **Solicitação já devolvida** relida na recepção cai na mensagem genérica "Nenhum registro encontrado…" — deveria dizer "solicitação devolvida em dd/mm por NC X".
5. **Patologista designado** só é pedido para HP; para os demais tipos o protótipo grava silenciosamente "Dr. Bruno Patologista". **Residente** é sempre "Dra. Carla Residente" (fixo). Validar quem designa patologista/residente e quando.
6. **Caso original (RI)** é texto livre sem validação de existência/formato.
7. **Urgente?** não tem valor padrão (obriga escolha) — confirmar se deve iniciar como "Não".
8. **Quantidade > 1** cria amostras `-F2…`; confirmar se cada frasco vira amostra separada ou se a granularidade vem do AGHU (spec: `item_solicitacao_aghu` ainda em validação).
9. **Tipo de exame**: IH não é selecionável na recepção (só via complementar). A spec prevê "exames recebidos de fora" com etapas `CONCLUIDA_EXTERNAMENTE` — não contemplado.
10. **Etiqueta**: código de barras é simulado; definir simbologia real (Code128/DataMatrix), tamanho 50×25 mm, conteúdo (iniciais do paciente?) e impressora térmica.
11. **Integração AGHU**: lembrete manual "registrar o recebimento no AGHU" — confirmar se haverá escrita no AGHU. O caso guarda `sol.statusAghu:'Solicitado'` enquanto os casos semeados mostram "Recebido no SAP" (inconsistência).
12. **Plantão de congelação**: apenas loga no histórico (patologista de plantão fixo); definir como acionar de fato (telefone, notificação).
13. Não há tela/fluxo para "Material complementar" chegar pela recepção e ser **vinculado a caso existente** (o toast promete "A nova amostra será vinculada ao caso pela recepção", mas a recepção não tem esse modo).
14. Não há busca/filtro na lista de solicitações pendentes nem tratamento de AGHU com muitas solicitações.
15. O passo 2 não oferece "Voltar" além de "Ler outra etiqueta" (que descarta tudo).

### Consulta
16. Título divergente: menu "Consulta de casos" × H1 "Consulta e pesquisa de casos" × título de página "Consulta de casos".
17. Ordenação fixa (urgentes + entrada desc.); a seta na coluna "Entrada" sugere ordenação clicável que não existe.
18. Filtros não incluem: setor/etapa atual, origem/unidade, médico solicitante, intervalo de datas personalizado, indicadores (rascunho/estagnado/retrabalho).
19. Exportação CSV de dados de paciente por qualquer perfil (exceto gestor) — validar política LGPD/auditoria da exportação (não gera audit log).
20. Paginação fixa de 10 itens, sem seletor de tamanho.
21. Rejeições na recepção (sem caso) não aparecem na Consulta.

### Rejeições e devoluções
22. Qualquer perfil (inclusive consulta/gestor) altera "Resolvido?" — definir quem pode.
23. Sem exportação, busca textual, paginação ou detalhe do registro (CMCE não é exibido na tabela).
24. Filtro "Etapa identificada" não lista Congelação, IHQ, Arquivo, Triagem.
25. Cancelamentos não aparecem aqui — confirmar se a tela deve consolidar "rejeições, devoluções e cancelamentos" (RF021 cobre ambos).
26. O nome da tela sugere distinção "rejeição" (na recepção, sem caso) × "devolução" (caso já aberto), mas a UI não diferencia visualmente — talvez coluna/badge "Rejeição na recepção" vs "Devolução de caso".

### Gerais / arquitetura
27. Protótipo é React (dc-runtime) com estilos inline; implementar em Vue 3 + Tailwind + Pinia reaproveitando tokens de cor/medidas da §2.
28. Seletor "Visualizar como" é recurso de demonstração; no sistema real o perfil vem do RBAC local (usuário com múltiplos perfis precisa de seletor de perfil ativo?).
29. Versão exibida no rodapé da sidebar: `v0.1.0` (atende requisito SemVer do AGENTS.md).
30. IPs de auditoria são simulados (`10.32.14.(20+índice do perfil)`).
31. Gestor oculta dados de paciente — validar se outros perfis (ex.: arquivo, processamento) também deveriam ver menos dados.
32. Indicadores são estáticos (não calculados a partir dos casos).
