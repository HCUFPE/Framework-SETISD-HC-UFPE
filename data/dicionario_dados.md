# Dicionário de dados — Solicitações de exames (vw_solicitacao_atualizado)

- **Registros (linhas):** 32.134 — cada linha é uma amostra/exame de uma solicitação
- **Colunas:** 17
- **Solicitações distintas:** 21.176
- **Pacientes distintos (por prontuário):** 11.996
- **Período das solicitações:** 01/01/2025 a 16/09/2026
- **Chave única da linha:** `codigo_solicitacao` + `numero_amostra` (sem duplicatas)

## Resumo dos campos

| # | Campo | Tipo | Valores distintos | Vazios | Categórico? |
|---:|---|---|---:|---:|---|
| 1 | `codigo_solicitacao` | inteiro (ID) | 21.176 | 0 | Não |
| 2 | `numero_amostra` | inteiro | 30 | 0 | Sim |
| 3 | `cod_status_item` | texto (código) | 8 | 0 | Sim |
| 4 | `status_item_exame` | texto | 8 | 0 | Sim |
| 5 | `data_solicitacao` | data (dd/mm/aaaa) | 525 | 0 | Não |
| 6 | `nome_paciente` | texto (iniciais) | 7.752 | 0 | Não |
| 7 | `data_nascimento` | data (dd/mm/aaaa) | 10.132 | 0 | Não |
| 8 | `prontuario` | inteiro (8 dígitos) | 11.996 | 1.509 | Não |
| 9 | `especialidade` | texto | 272 | 4.135 | Sim |
| 10 | `convenio` | texto | 1 | 0 | Sim |
| 11 | `origem` | texto | 4 | 0 | Sim |
| 12 | `unidade` | texto | 76 | 0 | Sim |
| 13 | `codigo_lab` | inteiro (código) | 5 | 0 | Sim |
| 14 | `informacoes_clinica` | texto livre | 16.368 | 39 | Não |
| 15 | `sigla_exame` | texto (código) | 12 | 0 | Sim |
| 16 | `nome_exame` | texto | 10 | 0 | Sim |
| 17 | `descricao_material` | texto livre | 14.105 | 380 | Não |

## Detalhamento por campo

### 1. `codigo_solicitacao` — Código da solicitação
Identificador da solicitação (6 a 7 dígitos, de 771982 a 1479445). Uma solicitação pode ter várias linhas (amostras).
- Exemplos: `1109703`, `1135455`, `1178390`

### 2. `numero_amostra` — Número da amostra
Sequencial da amostra dentro da solicitação, de **1 a 30**.
- Exemplos: `1`, `2`, `5`
- Distribuição: 1: 20.717; 2: 5.038; 3: 2.349; 4: 1.414; 5: 962; 6: 698; 7: 265; 8: 206; 9: 154; 10: 134; 11: 56; 12: 39; 13: 26; 14: 19; 15: 14; 16: 10; 17: 6; 18: 5; 19: 5; 20: 5; 21: 2; 22: 2; 23: 1; 24: 1; 25: 1; 26: 1; 27: 1; 28: 1; 29: 1; 30: 1

### 3. `cod_status_item` e 4. `status_item_exame` — Status do exame
Os dois campos são equivalentes (código ↔ descrição). **Todas as possibilidades:**

| Código | Status | Registros |
|---|---|---:|
| LI | LIBERADO | 24.959 |
| AC | A COLETAR | 4.567 |
| EX | EXECUTANDO | 763 |
| AE | AREA EXECUTORA | 732 |
| CA | CANCELADO | 644 |
| CO | COLETADO | 418 |
| EC | EM COLETA | 40 |
| PE | PENDENTE | 11 |

### 5. `data_solicitacao` — Data da solicitação
Formato dd/mm/aaaa, de 01/01/2025 a 16/09/2026 (525 dias distintos).
- Exemplos: `22/04/2026`, `05/09/2026`, `12/07/2025`

### 6. `nome_paciente` — Nome do paciente (anonimizado)
Apenas as iniciais do nome, separadas por ponto.
- Exemplos: `R.D.C.A.D.C.`, `T.G.D.S.D.M.`, `S.B.D.S.`

### 7. `data_nascimento` — Data de nascimento
Formato dd/mm/aaaa, de 23/03/1915 a 13/09/2026.
- Exemplos: `28/01/1952`, `02/08/1950`, `29/04/1971`

### 8. `prontuario` — Número do prontuário
Identificador do paciente no hospital (8 dígitos). **Vazio em 1.509 registros**, todos de origem *Paciente Externo*.
- Exemplos: `19909191`, `11615200`, `15090160`

### 9. `especialidade` — Especialidade solicitante
272 valores distintos. **Vazio em 4.135 registros** (exatamente os de origem *Paciente Externo*).
- Exemplos: `CIRURGIA GERAL`, `DERMATOLOGIA - ONCOLOGIA CUTANEA`, `GINECOLOGIA - TGI - COLPOSCOPIA`

<details>
<summary>Todas as especialidades (clique para expandir)</summary>

| Especialidade | Registros |
|---|---:|
| (vazio) | 4.135 |
| ENDOSCOPIA | 3.013 |
| CIRURGIA ONCOLOGICA | 1.819 |
| CIRURGIA GERAL | 1.784 |
| DERMATOLOGIA | 1.656 |
| ONCOLOGIA - MASTOLOGIA | 1.644 |
| GINECOLOGIA | 1.232 |
| GINECOLOGIA - TGI - COLPOSCOPIA | 1.226 |
| UROLOGIA MARCAÇÃO DE CIRURGIA | 1.010 |
| UROLOGIA | 986 |
| ONCOLOGIA CLINICA | 896 |
| GASTROENTEROLOGIA | 712 |
| OTORRINOLARINGOLOGIA | 675 |
| OBSTETRÍCIA | 663 |
| CIRURGIA PLASTICA | 578 |
| HEMATOLOGIA | 508 |
| CLINICA MEDICA | 486 |
| GASTROENTEROLOGIA - DOENÇA INF INTESTINAL | 478 |
| GINECOLOGIA - TGI - ALTO GRAU | 415 |
| NEFROLOGIA | 284 |
| PEDIATRIA | 260 |
| OFTALMOLOGIA | 252 |
| GINECOLOGIA - TGI - VULVA | 246 |
| CIRURGIA TORACICA | 244 |
| GINECOLOGIA - TGI - BAIXO GRAU | 224 |
| DERMATOLOGIA - ONCOLOGIA CUTANEA | 202 |
| DOENÇAS INFECTO PARASITARIAS | 194 |
| CIRURGIA DE CABECA E PESCOCO | 186 |
| PEDIATRIA - GASTRO | 181 |
| PROCTOLOGIA | 178 |
| GINECOLOGIA - HISTEROSCOPIA CIRÚRGICA | 177 |
| DIP ESPECIAL | 171 |
| GASTROENTEROLOGIA - INTESTINOS | 160 |
| HEMATOLOGIA - QUIMIOTERAPIA | 152 |
| CIRURGIA PEDIATRICA | 151 |
| URO APAC | 148 |
| GASTROENTEROLOGIA - HEPATOLOGIA | 143 |
| REGULADOS - CIRURGIA GERAL | 141 |
| GINECOLOGIA - TGI - RETORNO VULVA | 124 |
| ENDOCRINOLOGIA - TIREOIDE | 111 |
| MASTOLOGIA | 106 |
| CIRURGIA BARIATRICA | 104 |
| GERIATRIA | 104 |
| UROLOGIA - PRE-OP | 103 |
| REUMATOLOGIA - LUPUS | 101 |
| GINECOLOGIA - TGI - CAF | 93 |
| NEUROCIRURGIA | 89 |
| ORTOPEDIA E TRAUMATOLOGIA | 87 |
| TRANSPLANTE RENAL | 87 |
| OTORRINOLARINGOLOGIA - POS-OPERATORIO | 86 |
| REGULADOS - CLINICA MEDICA | 85 |
| UROGINECOLOGIA | 79 |
| GASTROENTEROLOGIA - ESQUISTOSSOMOSE | 73 |
| GINECOLOGIA - TGI - BAIXO E ALTO GRAU | 72 |
| REUMATOLOGIA | 71 |
| CARDIOLOGIA | 69 |
| GINECOLOGIA - TRIAGEM | 67 |
| NEUROLOGIA | 66 |
| GINECOLOGIA - ONCO | 61 |
| REGULADOS - GASTROENTEROLOGIA | 56 |
| REUMATOLOGIA - SINDROME DE SJOGREN | 55 |
| PNEUMOLOGIA | 54 |
| GINECOLOGIA - DISFUNÇÃO DO ASSOALHO PÉLVICO | 53 |
| GINECOLOGIA (RESIDENTES) | 51 |
| REGULADOS - DIP | 51 |
| GINECOLOGIA - TGI - 1ª VEZ PATOLOGIA CERVICAL | 51 |
| REGULADOS - REUMATOLOGIA | 49 |
| GINECOLOGIA - LAPAROSCOPIA | 48 |
| ALERGIA E IMUNOLOGIA | 48 |
| UROLOGIA RETORNO CIRURGICO | 47 |
| PROCTOLOGIA - CITOLOGIA E COLPOSCOPIA ANAL | 47 |
| GASTROENTEROLOGIA - ESOFAGO | 46 |
| DERMATOLOGIA - FOTOTERAPIA | 45 |
| OBSTETRÍCIA - MOL. TROFOBLÁTICA GESTACIONAL | 43 |
| DERMATOLOGIA - MICOSES TROPICAIS | 43 |
| UROLOGIA TRIAGEM | 43 |
| DERMATOLOGIA - HANSENIASE | 42 |
| DERMATOLOGIA - CIRURGIA | 41 |
| REGULADOS - CIRURGIA PEDIATRICA | 40 |
| GERIATRIA - NASS | 39 |
| NEONATOLOGIA | 39 |
| REGULADOS - HEMATOLOGIA | 37 |
| GINECOLOGIA - TGI - VOLTA PATOLOGIA CERVICAL | 36 |
| TOXICIDADE A QUIMIOTERAPICO E IMUNOSSUPRESSOR | 36 |
| CIRURGIA VASCULAR | 35 |
| ENDOCRINOLOGIA - TRIAGEM | 34 |
| ENDOCRINOLOGIA - DIABETES | 34 |
| GINECOLOGIA - TGI - VOLTA BAIXO GRAU | 32 |
| UROLOGIA HORMONIOTERAPIA | 31 |
| DERMATOLOGIA - UNHAS E CABELOS | 30 |
| REUMATOLOGIA - ESCLEROSE SISTEMICA | 30 |
| ONCOLOGIA CLINICA - TELEMEDICINA | 29 |
| UROLOGIA ONCO | 29 |
| GINECOLOGIA - TRIAGEM DA ENDOSCOPIA | 28 |
| DERMATOLOGIA - REUNIÃO CLÍNICA | 25 |
| REUMATOLOGIA - ESPONDILOARTRITES | 24 |
| REUMATOLOGIA - MIOPATIA INFLAMATÓRIA | 24 |
| OTORRINOLARINGOLOGIA - RINOLOGIA | 23 |
| REUMATOLOGIA - ARTRITE REUMATOIDE | 22 |
| REGULADOS - PEDIATRIA | 21 |
| TRIAGEM OBSTETRICA | 21 |
| ALERGIA - ASMA E CONJUNTIVITE | 21 |
| REGULADOS - NEURO CLINICO | 21 |
| ONCOLOGIA - GENETICA | 21 |
| PRE-EXAME ENDOSCOPIO | 21 |
| GINECOLOGIA - CLIMATÉRIO | 20 |
| ONCOLOGIA - GERIATRIA | 20 |
| OCI PROGRESSAO DA AVAL DIAG CANCER DE MAMA II | 20 |
| OFTALMOLOGIA - GLAUCOMA | 19 |
| DERMATOLOGIA - LEISHMANIOSE | 18 |
| ENDOCRINOLOGIA | 18 |
| DERMATOLOGIA - IMUNOSSUPRESSORES | 17 |
| DERMATOLOGIA - HIDRADENITE | 17 |
| ANESTESIOLOGIA - TELEMEDICINA | 16 |
| PNEUMOLOGIA - DOENÇAS INTERSTICIAIS | 16 |
| OTORRINOLARINGOLOGIA - APNEIA DO SONO | 16 |
| REUMATOLOGIA - OSTEOARTRITE | 15 |
| CIRURGIA VASCULAR - ESCLEROTERAPIA COM ESPUMA | 15 |
| DERMATOLOGIA - DERMATITE ATOPICA | 14 |
| CARDIO - RENAL | 14 |
| OFTALMOLOGIA - PLASTICA OCULAR | 13 |
| GASTROENTEROLOGIA - PANCREAS | 13 |
| DERMATOLOGIA - PSORIASE | 13 |
| BRONCOSCOPIA | 13 |
| ALERGIA - ALIMENTAR | 13 |
| REUMATOLOGIA - OSTEOPOROSE | 13 |
| ENDOCRINOLOGIA - PEDIATRIA | 13 |
| ENDOCRINOLOGIA - PRE-OP BARIATRICA | 12 |
| REGULADOS - ONCO CLINICA | 12 |
| ALERGIA - AUTOIMUNIDADE | 12 |
| PNEUMOLOGIA - ASMA | 12 |
| ALERGIA - ERRO INATO DA IMUNIDADE | 12 |
| ENFERMAGEM - ONCO - NAVEGACAO EM ONCOLOGIA | 11 |
| GASTROENTEROLOGIA - NODULOS HEPATICOS | 11 |
| GINECOLOGIA - MARCACAO CIRURGICA | 11 |
| ENDOCRINOLOGIA - NEURO | 11 |
| NEFROLOGIA - IRC | 11 |
| GINECOLOGIA - ALGIA PÉLVICA | 11 |
| REGULADOS - PNEUMOLOGIA | 10 |
| REUMATOLOGIA - INFUSAO | 10 |
| PNEUMOLOGIA - DPOC | 9 |
| CLINICA MEDICA - NASS | 9 |
| REUMATOLOGIA - FIBROMIALGIA | 9 |
| ENDOCRINOLOGIA - OBESIDADE | 9 |
| ALERGIA - IMUNODEFICIENCIA | 9 |
| DERMATOLOGIA - COSMIATRIA | 9 |
| REUMATOLOGIA - VASCULITES | 9 |
| CARDIOLOGIA - NASS | 9 |
| ESTABILIZACAO | 8 |
| ORTOPEDIA - JOELHO | 8 |
| ONCOLOGIA - OCI | 8 |
| GINECOLOGIA - PLANEJAMENTO FAMILIAR | 8 |
| GINECOLOGIA - NASS | 8 |
| ALERGIA - RINITE | 8 |
| REGULADOS - CIRURGIA VASCULAR | 8 |
| ONCOLOGIA | 8 |
| DOENCAS IMUNOMEDIADAS | 8 |
| NEFROLOGIA - GLOMERULONEFRITE | 7 |
| GERIATRIA - NAI | 7 |
| NUTRIÇÃO - NEFRO | 7 |
| ENDOCRINOLOGIA - GONADAS | 7 |
| REUMATOLOGIA - ARTRITE PSORIASICA | 7 |
| TELEMEDICINA INTERCONSULTA CLINICA | 7 |
| ENDOMETRIOSE CLÍNICA | 7 |
| ENDOCRINOLOGIA - OSTEOPOROSE | 6 |
| CARDIO - ONCOLOGIA | 6 |
| URO GINECO NEUROLOGIA | 6 |
| OBSTETRÍCIA - ALTO RISCO | 6 |
| TELEMEDICINA INTERCONSULTA CARGASHEMATO | 6 |
| CLINICA DA DOR | 6 |
| HEMATOLOGIA - EXAMES | 6 |
| REGULADOS - PSIQUIATRIA | 5 |
| OTORRINOLARINGOLOGIA - OTOLOGIA | 5 |
| TRANSPLANTE RENAL - RETORNO DOADOR DE RIM | 5 |
| CARDIO - ARRITMIA | 5 |
| NEUROLOGIA - PARKINSON | 5 |
| ORTOPEDIA - INFANTIL | 5 |
| GINECOLOGIA - ESPAÇO TRANS | 5 |
| REGULADOS - UROLOGIA | 5 |
| DERMATOLOGIA - NASS | 5 |
| TELEMEDICINA INTERCONSULTA COLOPROCTOLOGIA | 5 |
| REGULADOS - NEFROLOGIA | 5 |
| REUMATOLOGIA - GESTACAO (DRAI) | 5 |
| OFTALMOLOGIA - PEDIATRIA | 5 |
| REUMATOLOGIA - ESPONDILOARTRITE E GOTA | 5 |
| GASTROENTEROLOGIA - DOENCA HEPATICA GORDUROSA | 5 |
| TELEMEDICINA EM GERIATRIA | 5 |
| OFTALMOLOGIA - RETINA | 4 |
| NEUROLOGIA - MUSCULAR | 4 |
| ORTOPEDIA - QUADRIL | 4 |
| OTORRINOLARINGOLOGIA - LARINGOLOGIA | 4 |
| DERMATOLOGIA - TELEMEDICINA | 4 |
| DIP PREP | 4 |
| DIP - INFECTOLOGIA HOSPITALAR | 4 |
| ENDOCRINOLOGIA - DIABETES TIPO 1 | 4 |
| DERMATOLOGIA PEDIATRICA | 4 |
| NEFROLOGIA - PESQUISA | 4 |
| CIRURGIA PLASTICA - TRIAGEM | 4 |
| ENDOCRINOLOGIA PEDIÁTRICA - OBESIDADE INFANT | 4 |
| NEUROLOGIA -ATAXIA | 4 |
| RADIOLOGIA INTERVENCIONISTA | 4 |
| PSIQUIATRIA - TRIAGEM - TELEMEDICINA | 4 |
| REGULADOS - CARDIOLOGIA | 4 |
| ALERGIA - INFUSAO | 4 |
| TRANSPLANTE RENAL - PRE-TRANSPLANTE | 3 |
| OFTALMOLOGIA - LASER - FOTOCOAGULACAO | 3 |
| TELEMEDICINA INTERCONSULTA INFPNEUDOR | 3 |
| PSIQUIATRIA | 3 |
| CARDIOLOGIA - PESQUISA CLINICA | 3 |
| TELEMEDICINA INTERCONSULTA ENDOCRINOLOGIA | 3 |
| CARDIO - RISCO CIRURGICO | 3 |
| ENDOCRINOLOGIA - CANCER DE TIREOIDE | 3 |
| OBSTETRÍCIA - PUERPÉRIO | 3 |
| UROLOGIA AULAS PRATICAS | 3 |
| GINECOLOGIA - DOENCAS BENIGNAS DA MAMA | 3 |
| HOSPITAL-DIA - ENFERMAGEM | 2 |
| ENFERMAGEM - TGI - COLPO - TRIAGEM | 2 |
| MEDICINA DO TRABALHO | 2 |
| ENFERMAGEM - ONCOLOGIA | 2 |
| ENDOCRINOLOGIA - DISLIPIDEMIA | 2 |
| NEUROLOGIA - CEFALEIA | 2 |
| OBSTETRÍCIA - DIABETES | 2 |
| ENDOCRINOLOGIA - ADRENAL | 2 |
| ONCOLOGIA - TRIAGEM | 2 |
| GERIATRIA - PRE OPERATORIO | 2 |
| NEFROLOGIA - GLOMERULOPATIA | 2 |
| ENDOCRINOLOGIA - PARATIREOIDE | 2 |
| ALERGIA - DERMATOSES ALERGICAS | 2 |
| TELEMEDICINA INTERCONSULTA GASTROENTEROLOGIA | 2 |
| OFTALMOLOGIA - CLOROQUINA | 2 |
| OTORRINOLARINGOLOGIA - VIDEOLARINGOSCOPIA | 2 |
| ALERGIA - DROGAS | 2 |
| ESPACO TRANS | 2 |
| NEFROLOGIA - DOENCA MINERAL OSSEA TX RENAL | 2 |
| GASTROENTEROLOGIA - BIOPSIA HEPATICA | 2 |
| PNEUMOLOGIA - BRONQUIECTASIA | 2 |
| ORTOPEDIA - MÃO | 2 |
| OFTALMOLOGIA - USG OCULAR | 2 |
| OCI AVAL DIAG INICIAL DE CANCER DE MAMA | 2 |
| PUERICULTURA - ADOLESCENTE | 1 |
| ORTOPEDIA - OMBRO | 1 |
| NUTRIÇÃO - NASS | 1 |
| OFTALMOLOGIA - VISAO SUBNORMAL | 1 |
| PSIQUIATRIA - TERAPIA FAMILIAR | 1 |
| SERVIÇO SOCIAL - CIRURGIA GERAL | 1 |
| NEUROLOGIA - DEMENCIA | 1 |
| NUTRICAO - OBESIDADE | 1 |
| ENFERMAGEM - PRÉ OPERATÓRIO | 1 |
| REUMATOLOGIA - CHIKUNGUNYA | 1 |
| ENDOCRINOLOGIA - ONCO | 1 |
| CIRURGIA UROLÓGICA | 1 |
| ACUPUNTURA | 1 |
| CIRURGIA PEDIÁTRICA - UROPEDIATRIA | 1 |
| NEFROLOGIA - ONCOLOGIA | 1 |
| REGULADOS - GERIATRIA | 1 |
| OFTALMOLOGIA - CORNEA CIRURGICA | 1 |
| ENFERMAGEM - CIRURGIA BARIÁTRICA | 1 |
| OTORRINOLARINGOLOGIA - OTONEURO | 1 |
| ENFERMAGEM - PRE-TRANSPLANTE | 1 |
| POS-CIRURGIA BARIATRICA | 1 |
| TRANSPLANTE RENAL - URO TRANSPLANTE | 1 |
| REUMATOLOGIA - SAAF | 1 |
| PSICOLOGIA - CIRURGIA GERAL | 1 |
| OFTALMOLOGIA - TUMOR OCULAR | 1 |
| PNEUMOLOGIA - PARECER | 1 |
| CIRURGIA DO APARELHO DIGESTIVO | 1 |
| OFTALMOLOGIA - DOENCA OCULAR TIREOIDEANA | 1 |
| PEDIATRIA - ENDOCRINO | 1 |
| PNEUMO-ONCO | 1 |
| CLINICA MEDICA - ENSINO | 1 |
| NEUROLOGIA - EPILEPSIA | 1 |
| HEBIATRIA | 1 |
| ANESTESIOLOGIA | 1 |

</details>

### 10. `convenio` — Convênio
Valor único em toda a base.

| Convênio | Registros |
|---|---:|
| SUS | 32.134 |

### 11. `origem` — Origem do paciente/solicitação
**Todas as possibilidades:**

| Origem | Registros |
|---|---:|
| Ambulatório | 14.291 |
| Internação | 10.118 |
| Paciente Externo | 4.135 |
| Cirurgia | 3.590 |

### 12. `unidade` — Unidade solicitante
76 valores distintos (enfermarias por andar/ala, ambulatórios, blocos e unidades de apoio). Obs.: três valores (`UAP: HISTOPATOLÓGICO`, `UAP: IMUNOHISTOQUÍMICA`, `UAP: CITOLOGIA CÉRVICO-VAGINAL`) vêm com um caractere invisível (zero-width space) no final — convém limpar antes de filtrar.
- Exemplos: `9º  SUL`, `ENDOSCOPIA`, `DERMATOLOGIA (AMBULATÓRIO)`

<details>
<summary>Todas as unidades (clique para expandir)</summary>

| Unidade | Registros |
|---|---:|
| 9º  SUL | 3.174 |
| GINECOLOGIA (AMBULATÓRIO) | 3.055 |
| UAP: HISTOPATOLÓGICO | 2.807 |
| ENDOSCOPIA | 2.671 |
| ONCOLOGIA (AMBULATÓRIO) | 2.459 |
| DERMATOLOGIA (AMBULATÓRIO) | 2.188 |
| 8º NORTE | 1.935 |
| UROLOGIA (AMBULATÓRIO) | 1.759 |
| GASTROENTEROLOGIA (AMBULATÓRIO) | 1.479 |
| 7 º SUL | 1.015 |
| BLOCO CIRURGICO | 895 |
| 8º SUL | 855 |
| UAP: IMUNOHISTOQUÍMICA | 678 |
| 5º NORTE | 595 |
| UDI: ULTRASSONOGRAFIA | 519 |
| HEMATOLOGIA (AMBULATÓRIO) | 505 |
| CIRURGIA GERAL (AMBULATÓRIO) | 392 |
| 10º NORTE | 376 |
| 6º SUL | 373 |
| CENTRO OBSTETRICO | 351 |
| 11º SUL | 348 |
| REUMATOLOGIA (AMBULATÓRIO) | 342 |
| ENDOCRINOLOGIA (AMBULATÓRIO) | 258 |
| UTI ADULTO | 238 |
| 11º NORTE | 236 |
| 10º SUL | 235 |
| OTORRINOLARINGOLOGIA (AMBULATÓRIO) | 219 |
| 9º NORTE | 209 |
| PEDIATRIA (AMBULATÓRIO) | 192 |
| CLÍNICA MÉDICA (AMBULATÓRIO) | 191 |
| INFECTOLOGIA (AMBULATÓRIO) | 179 |
| 4º NORTE | 150 |
| OFTALMOLOGIA (AMBULATÓRIO) | 115 |
| CIRURGIA BARIATRICA | 93 |
| PNEUMOLOGIA (AMBULATÓRIO) | 92 |
| ALERGIA E IMUNOLOGIA (AMBULATÓRIO) | 83 |
| GERIATRIA (AMBULATORIO) | 76 |
| CARDIOLOGIA (AMBULATÓRIO) | 72 |
| NÚCLEO DO SERVIDOR (AMBULATÓRIO) | 71 |
| OBSTETRÍCIA (AMBULATÓRIO) | 63 |
| NEFROLOGIA (AMBULATÓRIO) | 62 |
| CIRURGIA DE CABECA E PESCOCO | 54 |
| PROCTOLOGIA (AMBULATORIO) | 52 |
| CIRURGIA PLÁSTICA (AMBULATÓRIO) | 39 |
| CIRURGIA VASCULAR (AMBULATÓRIO) | 37 |
| UAP: CITOLOGIA GERAL | 37 |
| BLOCO DERMATO | 36 |
| UAC: SOROLOGIA | 30 |
| NEUROLOGIA (AMBULATÓRIO) | 29 |
| UAP: CONGELAÇÃO | 22 |
| ORTOPEDIA (AMBULATÓRIO) | 20 |
| UAP: CITOLOGIA CÉRVICO-VAGINAL | 20 |
| TRANSPLANTE (AMBULATÓRIO) | 18 |
| ANESTESIOLOGIA (AMBULATÓRIO) | 17 |
| CIRURGIA TORÁCICA (AMBULATÓRIO) | 17 |
| UCI NEONATAL | 12 |
| NUCLEO DE TELESSAUDE | 9 |
| NUTRIÇÃO | 8 |
| URGENCIA E EMERGENCIA | 8 |
| UTI NEONATAL | 8 |
| CIRURGIA PEDIÁTRICA (AMBULATÓRIO) | 8 |
| PSIQUIATRIA (AMBULATÓRIO) | 7 |
| BRONCOSCOPIA | 6 |
| CLINICA DA DOR (AMBULATÓRIO) | 6 |
| 7º NORTE | 5 |
| ESPAÇO TRANS (AMBULATÓRIO) | 5 |
| OFTALMO GERAL | 4 |
| HEMODINAMICA - PDT | 4 |
| HOSPITAL - DIA | 2 |
| SAUDE OCUPACIONAL E SEGURANCA DO TRABALHO | 2 |
| HEMODIALISE | 2 |
| ENFERMAGEM | 1 |
| ACUPUNTURA (AMBULATÓRIO) | 1 |
| UAC: EXAMES EXTERNOS | 1 |
| UCI CANGURU | 1 |
| PUERICULTURA (AMBULATÓRIO) | 1 |

</details>

### 13. `codigo_lab` — Código do laboratório/setor executor
**Todas as possibilidades** (com os exames associados a cada código):

| Código | Exames (sigla) | Registros |
|---|---|---:|
| 139 | CCVM | 2.456 |
| 203 | CITOP, CPMAM | 1.038 |
| 205 | CONGE | 480 |
| 207 | APECR, CITO, COLUT, COUT2, HPDER, MBIOP, MPCIR | 26.192 |
| 209 | IMUHI | 1.968 |

### 14. `informacoes_clinica` — Informações clínicas
Texto livre digitado pelo solicitante (hipótese diagnóstica, motivo, histórico). 16.368 valores distintos; vazio em 39 registros. Para *Paciente Externo* costuma vir no padrão `Paciente Externo: <material>`.
- Exemplos: `MIOMAS UTERINOS`, `rastreio`, `INVESTIGAÇÃO DE DISPEPSIA. ACHADO ENDOSCÓPICO DE ATROFIA GÁSTRICA.`

### 15. `sigla_exame` e 16. `nome_exame` — Exame solicitado
**Todas as possibilidades** (sigla → nome → laboratório). Atenção: `nome_exame` tem 10 valores para 12 siglas — `MBIOP`/`MPCIR` compartilham *ANATOMOPATOLÓGICO - MAMA* e `COLUT`/`COUT2` compartilham *ANATOMOPATOLÓGICO - COLO UTERINO*.

| Sigla | Nome do exame | Cód. lab | Registros |
|---|---|---|---:|
| APECR | ANATOMOPATOLÓGICO - PEÇA CIRÚRGICA | 207 | 20.443 |
| CCVM | EXAME CITOPATOLÓGICO CÉRVICO-VAGINAL/MICROFLORA | 139 | 2.456 |
| HPDER | HISTOPATOLOGICO DERMATOLOGIA | 207 | 2.133 |
| IMUHI | IMUNO-HISTOQUÍMICA | 209 | 1.968 |
| MBIOP | ANATOMOPATOLÓGICO - MAMA | 207 | 1.692 |
| MPCIR | ANATOMOPATOLÓGICO - MAMA | 207 | 1.129 |
| CITOP | CITOPATOLÓGICO | 203 | 1.013 |
| CONGE | AP- EXAME TRANSOPERATÓRIO DE CONGELAÇÃO (PATOLOGIA) | 205 | 480 |
| CITO | CITOLOGIA ONCÓTICA | 207 | 380 |
| COUT2 | ANATOMOPATOLÓGICO - COLO UTERINO | 207 | 298 |
| COLUT | ANATOMOPATOLÓGICO - COLO UTERINO | 207 | 117 |
| CPMAM | CITOPATOLOGICO DE MAMA | 203 | 25 |

### 17. `descricao_material` — Descrição do material/amostra
Texto livre com o material enviado (órgão, peça, localização, frasco). 14.105 valores distintos; vazio em 380 registros (todos do exame `CITO` — Citologia Oncótica).
- Exemplos: `MIOMATOSES UTERINAS`, `VESICULA BILIAR`, `MAMA DIREITA 10H`

## Dados derivados (calculáveis a partir das colunas)

| Dado derivado | Como obter | Exemplos / resumo |
|---|---|---|
| Idade do paciente na solicitação | `data_solicitacao` − `data_nascimento` | mediana 54 anos; mín. 0, máx. 111 |
| Faixa etária | agrupamento da idade | `0–17`, `18–59`, `60+` |
| Amostras por solicitação | contagem de linhas por `codigo_solicitacao` | média 1,52; máx. 30 |
| Volume por período | `data_solicitacao` agrupada por dia/mês/ano | ex.: jan/2025, fev/2025… set/2026 |
| Dia da semana da solicitação | a partir de `data_solicitacao` | `segunda`, `sexta`, `sábado` |
| Pacientes recorrentes | solicitações distintas por `prontuario` | pacientes com 1, 2, 3+ solicitações |
| Taxa de liberação / cancelamento / pendência | proporção de `status_item_exame` | ex.: LIBERADO ≈ 77,7% |
| Lateralidade / sítio anatômico | extração por texto em `descricao_material` | `DIREITA`, `ESQUERDA`, `MAMA`, `COLO UTERINO` |
| Mapeamento exame × especialidade × unidade × origem | cruzamento das colunas categóricas | ex.: CCVM ↔ GINECOLOGIA (AMBULATÓRIO) |

## Observações de qualidade

- `especialidade` e `prontuario` são vazios apenas para *Paciente Externo*.
- `descricao_material` é vazio apenas para o exame `CITO`.
- `informacoes_clinica` é vazio em 39 registros (38 de `IMUHI`, 1 de `APECR`).
- Três valores de `unidade` contêm caractere invisível (U+200B) no final.
- `unidade` tem grafias inconsistentes de andares (`9º  SUL` com dois espaços, `7 º SUL`) e de ambulatório (`(AMBULATÓRIO)` vs `(AMBULATORIO)`).
- `convenio` é constante (`SUS`) — não discrimina registros.