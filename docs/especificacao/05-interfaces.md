# Interfaces e Integrações

## 1. Tela de Recebimento de Amostras
Rota `/recebimento`, disponível no menu lateral como "Recebimento" para usuários autenticados.

* **Busca:** um único campo aceita o código lido ou digitado. O campo recebe foco ao abrir a tela e fica sempre visível.
* **Lista inicial:** aparece ao abrir a tela, antes de qualquer pesquisa, com 10 solicitações por página, da mais recente para a mais antiga. Mostra código, data, nome, idade, prontuário, origem, clínica, unidade, bancadas, amostras recebíveis e situação, além do nº interno quando já existe. Não mostra informações clínicas. Clicar em uma linha abre a conferência, pelo mesmo fluxo da leitura.
* **Paginação da lista:** botões Anterior e Próxima e botões numerados com a primeira e a última página, a atual em destaque e as vizinhas dela; os saltos aparecem como reticências. A tela mostra todas as solicitações, sem filtro.
* **Situação na lista:** Aguardando recebimento; Recebida em parte; Recebida; Devolvida à origem (pode ser recebida de novo); Sem amostra recebível.
* **Resumo da solicitação:** faixa compacta com código, situação, selo "Urgente" e todas as colunas da view: nome, prontuário, nascimento e idade, data da solicitação, origem, clínica, unidade, convênio e informações clínicas. O texto clínico preserva as quebras de linha e, se for longo, começa recolhido, com a opção "Ler tudo". "Voltar para a lista" encerra a conferência sem gravar.
* **Urgente:** aparece quando um exame foi gravado como urgente ou quando há amostra de CO (CARE-RF007).
* **Devolução pendente:** um alerta acima das amostras mostra o motivo de cada bancada devolvida e ainda não resolvida.
* **Amostras:** uma linha por amostra, com número, bancada, nome do exame, sigla, código do laboratório, material, status e código do status no AGHU e opção de receber. A amostra já recebida não mostra a caixa: mostra "Recebida", quem conferiu e quando, e o material informado na recepção.
* **Barra de ações:** fica fixa no rodapé da área visível enquanto a tabela rola, com o progresso ("2 de 12 amostras marcadas · Checklist 1 de 3"), "Registrar não conformidade" e "Concluir recebimento".
* **Histórico no sistema:** abaixo das amostras, cada exame mostra situação, usuário, data e hora, urgência, quantidade de peças, procedimento, HP de origem e amostras recebidas. Cada não conformidade mostra motivo, observação, nº no CMCE, médico solicitante e se foi resolvida, por quem e quando.
* **Checklist do recebimento:** é único para todas as amostras marcadas, com três itens: siglas × conteúdo, descrições × frascos e nº de recipientes. Começa sempre desmarcado e aparece quando há amostra marcada. Marcar uma amostra depois de confirmar o checklist o desmarca, porque ela ainda não foi conferida; desmarcar uma amostra o mantém.
* **Amostra sem descrição no AGHU:** a linha pede o material do frasco, obrigatório para receber.
* **Amostra bloqueada:** quando o status do item não permite o recebimento, o status não está configurado, falta o prontuário fora de Paciente Externo ou o exame da bancada já foi recebido, a linha mostra o motivo e fica desabilitada.
* **Dados do HP:** aparecem quando há amostra HP marcada, todos obrigatórios: quantidade de peças (inteiro a partir de 1), urgência (Sim ou Não) e procedimento (lista).
* **HP de origem da IHQ:** aparece quando há amostra IHQ marcada. É opcional e, se preenchido, usa o formato `HP-AAAA/N`.
* **Concluir recebimento:** habilitado só quando há amostra marcada e estão completos o checklist do recebimento, o material pendente e os dados obrigatórios. Depois de concluir, o nº interno aparece em destaque (um por bancada), a lista volta atualizada e o foco retorna ao campo.
* **Registrar não conformidade:** abre um modal com motivo e observação, obrigatórios, e nº no CMCE e médico solicitante, opcionais. Ao confirmar, a tela mostra a devolução, a lista volta atualizada e o foco retorna ao campo.

## 2. Hardware

### Leitor de código de barras
A pistola funciona como teclado: envia os caracteres do código e depois Enter. A tela foi feita para esse uso, sem mouse:

* Enter dispara a busca; leituras repetidas durante uma busca são ignoradas.
* Depois de cada busca, o foco permanece no campo com o texto selecionado, então a próxima leitura substitui o valor anterior.
* Ler outro frasco da solicitação aberta rola até a amostra lida, marca a linha com "Lida agora" e **mantém o que já foi preenchido**. O foco continua no campo.

### Formato do código lido
Interpretado por `interpretar_codigo_lido()`, em `src/helpers/etiqueta_helper.py` (RNF002). O código da solicitação tem 6 ou 7 dígitos, e os exemplos abaixo são inventados. O formato real da etiqueta ainda será confirmado.

| Entrada | Exemplo | Resultado |
| :--- | :--- | :--- |
| Só o código | `9000101` | Solicitação |
| Código + amostra em 3 dígitos | `9000101001` | Solicitação e amostra 1 |
| Código, hífen e amostra | `9000101-1` | Solicitação e amostra 1 |
| Amostra zero, 8 dígitos ou outro formato | `99000101` | HTTP 422 |

Oito dígitos são recusados por serem ambíguos e por terem o tamanho do prontuário, que pode ser bipado por engano.

### Etiquetadora e impressoras térmicas
Fora do escopo desta feature (RF008, RF009).

## 3. Software: integração com o AGHU
O sistema só **lê** o AGHU (RN-01, RNF001). Não existem endpoint, método ou SQL de escrita no AGHU.

### Contrato da `SolicitacaoProviderInterface`
Arquivo: `src/providers/interfaces/solicitacao_provider_interface.py`.

```python
async def obter_solicitacao_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]
```

Retorna `None` quando o código não existe. Quando existe, retorna o formato abaixo, com dados inventados:

```json
{
  "codigo": "9000101",
  "data_solicitacao": "2026-03-02",
  "nome_paciente": "Z.Y.X.",
  "data_nascimento": "1980-05-14",
  "prontuario": "99000101",
  "especialidade": "CIRURGIA GERAL",
  "origem": "Internação",
  "unidade": "9º SUL",
  "informacoes_clinica": "Texto clínico fictício para teste.",
  "itens": [
    {
      "numero_amostra": 1,
      "codigo_lab": "207",
      "sigla_exame": "APECR",
      "nome_exame": "ANATOMOPATOLÓGICO - PEÇA CIRÚRGICA",
      "descricao_material": "Fragmento fictício de cólon",
      "cod_status_item": "CO",
      "status_item_exame": "COLETADO"
    }
  ]
}
```

A conversão de `codigo_lab` em bancada e a regra de status são regras de negócio e ficam no controller.

Para a lista, `listar_solicitacoes(pagina, por_pagina, codigos_status, codigos_lab)` retorna `{"total": int, "solicitacoes": [...]}`, com cada solicitação nesse mesmo formato. O CSV é relido a cada consulta e só a página pedida é montada, sem guardar dados de pacientes em memória.

| Implementação | Situação |
| :--- | :--- |
| `SolicitacaoCsvProvider` | Em uso. Lê o arquivo indicado em `SOLICITACAO_CSV_PATH` (padrão: `data/solicitacoes_aghu_exemplo.csv`) |
| `SolicitacaoPostgresProvider` | Consulta `vw_solicitacao` com `src/providers/sql/solicitacao/obter_solicitacao.sql`. Testado com sessão simulada, ainda não no banco real; o schema e os tipos estão como `TODO` |

A fonte de dados é escolhida pela constante `STRATEGY` em `src/routers/recebimento.py`. Os dois providers usam `montar_solicitacao()`, de `solicitacao_mapeamento.py`, que remove caracteres invisíveis e espaços repetidos e converte as datas. Nas informações clínicas, as quebras de linha são preservadas.

### Layout do CSV (`vw_solicitacao`)
> **O arquivo real tem dados de pacientes e nunca vai para o Git.** `data/vw_solicitacao_atualizado.csv` está no `.gitignore`. Para usá-lo, aponte `SOLICITACAO_CSV_PATH` para ele no `.env`. Os testes usam `data/solicitacoes_aghu_exemplo.csv`, com o mesmo cabeçalho e dados inventados.

Formato: separado por vírgula, UTF-8 (com ou sem BOM), com cabeçalho e **uma linha por amostra**. Os dados do paciente se repetem em cada linha. Se faltar coluna, a API responde 503. O dicionário das colunas está em `04-modelo-dados.md`.

### Mapeamento de bancadas
Fica na tabela `bancadas_laboratorio`, sem regra no código. Laboratório sem mapeamento ou inativo não é recebível.

| `codigo_lab` | Bancada | Prefixo do nº interno | Siglas no CSV atual |
| :--- | :--- | :--- | :--- |
| 207 | HP | `HP` | APECR, HPDER, MBIOP, MPCIR, COLUT, COUT2, CITO |
| 203 | CG | `CG` | CITOP, CPMAM |
| 139 | CCV | `CCV` | CCVM |
| 205 | CO | `CO` | CONGE |
| 209 | IHQ | `IH` | IMUHI |

O nº interno é **por bancada**: uma solicitação com duas bancadas gera dois exames e dois números. Duas siglas na mesma bancada ficam em um só exame.

### Status do item
Fica na tabela `status_item_aghu`, com os nomes do AGHU (RNF003). A regra vale por item, e status desconhecido bloqueia. A não conformidade é aceita em qualquer status.

| Código | Nome no AGHU | Permite o recebimento |
| :--- | :--- | :---: |
| `AC` | A COLETAR | Sim |
| `EC` | EM COLETA | Sim |
| `CO` | COLETADO | Sim |
| `AE` | AREA EXECUTORA | Sim |
| `PE` | PENDENTE | Sim |
| `EX` | EXECUTANDO | Não |
| `LI` | LIBERADO | Não |
| `CA` | CANCELADO | Não |

### Planilha substituída (RN-07)
| Coluna da planilha | Origem | Destino |
| :--- | :--- | :--- |
| Nº interno | Sistema | `exames.numero_interno` |
| Código AGHU | AGHU | `exames.codigo_solicitacao` |
| Data de entrada | Sistema | `exames.recebido_em` |
| Nome | AGHU (só iniciais) | Lido do AGHU, não gravado |
| Registro | AGHU | `exames.prontuario` |
| Idade | Calculada de `data_nascimento` | Não gravada |
| A/E | Derivada de `origem` (a definir) | `exames.origem` |
| Clínica | AGHU (`especialidade`) | `exames.especialidade` |
| Material | AGHU, ou recepção se vazio | `amostras.descricao_material` ou `descricao_informada` |
| Quantidade de peças (HP) | Recepção | `exames.quantidade_pecas` |
| Urgência (HP) | Recepção, Sim ou Não | `exames.urgente` |
| Procedimento (HP) | Recepção, lista | `exames.procedimento_id` |
| Referência ao HP (IHQ) | Recepção | `exames.referencia_hp` |

| Registro de rejeição | Origem | Destino |
| :--- | :--- | :--- |
| Data | Sistema | `nao_conformidades.registrado_em` |
| Prontuário, nº no AGHU, origem, especialidade | AGHU | `exames` |
| Exame | AGHU | `amostras.sigla_exame` e `nome_exame` |
| Paciente | AGHU | Lido do AGHU, não gravado |
| Nº no CMCE | Recepção, opcional | `nao_conformidades.numero_cmce` |
| Médico solicitante | Recepção, opcional | `nao_conformidades.medico_solicitante` |
| Inconformidade | Recepção, lista | `nao_conformidades.motivo_id` |
| Detalhamento | Recepção, obrigatório | `nao_conformidades.observacao` |
| Resolveu? | Sistema, ao receber de novo | `nao_conformidades.resolvida` |

## 4. API REST
Prefixo `/api/recebimento`. Todas as rotas exigem token (Default-Private Router) e respondem 401 sem ele. Os erros seguem o formato `{"detail": "mensagem"}`. Os esquemas JSON estão em [04-modelo-dados.md](04-modelo-dados.md).

**Perfil:** o perfil `RECEPCAO` (RF002) depende do RBAC local, que será uma feature própria. Hoje, qualquer usuário autenticado acessa estas rotas.

| Método e rota | Entrada | Saída | Erros |
| :--- | :--- | :--- | :--- |
| `GET /motivos-nao-conformidade` | Nenhuma | 200: lista de motivos ativos | 401 |
| `GET /procedimentos-hp` | Nenhuma | 200: lista de procedimentos ativos | 401 |
| `GET /solicitacoes` | `pagina` (padrão 1), `por_pagina` (padrão 10, máximo 100) e `somente_recebiveis` (padrão `true`; a tela envia `false`) | 200: página com total, total de páginas e resumo das solicitações. Página além do fim vem vazia | 400 parâmetro inválido; 401; 503 falha ao ler o CSV ou layout inválido |
| `GET /solicitacoes/{codigo}` | Código lido ou digitado | 200: paciente, clínica, situação, urgência, amostras e histórico completo dos exames | 400 caractere não permitido; 401; 404 solicitação ou amostra não encontrada; 422 código em formato inválido ou sem itens das 5 bancadas; 503 falha ao ler o CSV ou layout inválido |
| `POST /solicitacoes/{codigo}/recebimentos` | Amostras, os três itens do checklist, `dados_hp` e `referencia_hp` | 201: exames com nº interno | 400 corpo inválido ou valor fora do controle; 401; 404; 409 já recebida, informando o nº; 422 checklist incompleto, nenhuma amostra marcada, amostra inválida ou bloqueada, material ausente, dados de HP ausentes, procedimento ou referência inválidos; 503 banco ocupado, sem nada gravado |
| `POST /solicitacoes/{codigo}/nao-conformidades` | `motivo_id`, `observacao`, `numero_cmce` e `medico_solicitante` | 201: exames devolvidos, sem número | 400 corpo inválido; 401; 404; 409 todas as bancadas já recebidas; 422 motivo inválido ou observação vazia; 503 |

Os erros de validação de formato respondem 400 pelo handler global do framework. As regras de negócio respondem 422.
