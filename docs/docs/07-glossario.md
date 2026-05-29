# Glossário e Referências

## 1. Termos do Domínio Clínico

| Termo | Definição |
|---|---|
| **AGHU** | Aplicação de Gestão para Hospitais Universitários — sistema legado do HC/UFPE onde o prontuário legal do paciente é mantido. |
| **AIH** | Autorização de Internação Hospitalar — documento que autoriza e registra internações no SUS. |
| **BPA** | Boletim de Produção Ambulatorial — registro de atendimentos ambulatoriais para faturamento no SUS. |
| **Caderneta Digital** | Histórico longitudinal de crescimento do paciente com curvas de peso, altura e IMC. Equivalente digital da caderneta física de saúde da criança. |
| **Certbr** | Certificado digital emitido pela RNP (Rede Nacional de Ensino e Pesquisa) usado para assinatura digital de prontuários no AGHU. |
| **CID-10** | Classificação Internacional de Doenças, 10ª revisão — vocabulário controlado e oficial para diagnósticos. |
| **Egresso** | Tipo de entrada na fila: paciente com alta recente do HC em retorno de acompanhamento pós-internamento (15–20 dias). |
| **Encaminhamento Externo** | Tipo de entrada: paciente proveniente de UPA ou Unidade Básica de Saúde. |
| **Exame Físico por Sistema** | Avaliação estruturada dividida em 9 sistemas: Cabeça e pescoço, Olhos, Cardiovascular, Respiratório, Abdômen, Genitália, Pele, Membros e coluna, Neurológico. |
| **Ficha de Referência** | Documento gerado pelo sistema para entrega à família com dados do encaminhamento: especialidade, procedimento, prioridade e justificativa clínica. |
| **Fontanelas** | Espaços membranosos entre os ossos do crânio do bebê. Avaliadas no exame físico de cabeça e pescoço para pacientes com até 18 meses. |
| **HC** | Hospital das Clínicas — Hospital das Clínicas da UFPE, Pernambuco. O HC não possui emergência pediátrica. |
| **IMC** | Índice de Massa Corporal — calculado automaticamente pelo sistema: peso(kg) / altura(m)². |
| **Internação** | Tipo de entrada: paciente já internado no HC atendido em consulta ambulatorial. |
| **LGPD** | Lei Geral de Proteção de Dados (Lei 13.709/2018) — regula o tratamento de dados pessoais no Brasil. |
| **Marco de Desenvolvimento** | Habilidades esperadas para a faixa etária da criança (motor, linguagem, social, cognitivo). Avaliados em tabela por faixa etária; status: confirmado, não atingido, não avaliado. |
| **M-CHAT-R** | Modified Checklist for Autism in Toddlers, Revised — instrumento de rastreio de risco para Transtorno do Espectro Autista (TEA). Aplicável a crianças entre 16 e 30 meses. Score: ≤2 = baixo risco; 3–7 = médio risco (aplicar entrevista de seguimento); ≥8 = alto risco (encaminhar imediatamente). |
| **Percentil** | Posição da medição do paciente em relação à curva de referência populacional (ex: P50 = mediana). |
| **Perímetro Cefálico (PC)** | Medida da circunferência da cabeça — indicador de desenvolvimento neurológico. |
| **Prontuário** | Documento legal do paciente mantido no AGHU. Este sistema registra dados estruturados das consultas mas não substitui o prontuário legal. |
| **Reflexos Primitivos** | Reflexos neurológicos presentes no recém-nascido que desaparecem com a maturação. Avaliados no exame neurológico de pacientes com até 12 meses. |
| **Retorno** | Tipo de entrada: consulta de acompanhamento agendada. |
| **SID** | Código de sistema de informação específico do serviço (ex: Sistema de Informação sobre Nascidos Vivos). Preenchido quando houver código específico. |
| **TEA** | Transtorno do Espectro Autista — condição rastreada pelo M-CHAT-R em crianças de 16–30 meses. |
| **TCLE** | Termo de Consentimento Livre e Esclarecido — documento de consentimento do paciente/responsável para uso de dados. |

---

## 2. Termos Técnicos do Sistema

| Termo | Definição |
|---|---|
| **AD / Active Directory** | Serviço de diretório da Microsoft usado pelo HC para autenticação de usuários. |
| **AGHU Provider** | Implementação futura de `PacienteProviderInterface` que se conectará à API do AGHU. Troca de estratégia via `STRATEGY = "aghu"` no roteador. |
| **Alembic** | Ferramenta de migrations de banco de dados para SQLAlchemy. |
| **Axios** | Cliente HTTP usado no frontend Vue para chamadas à API FastAPI. |
| **CSV Provider** | Implementação de `PacienteProviderInterface` que lê dados de arquivos CSV. Usada em desenvolvimento e como fallback. |
| **FastAPI** | Framework Python assíncrono para construção de APIs REST. |
| **HttpOnly Cookie** | Cookie inacessível via JavaScript — usado para o refresh token JWT como proteção contra XSS. |
| **JWT** | JSON Web Token — token de autenticação de curta duração (15 minutos) emitido após login LDAP. |
| **LDAP3** | Biblioteca Python para comunicação com servidores LDAP/Active Directory. |
| **PatientContext** | Store Pinia no frontend que armazena o paciente ativo durante o fluxo de atendimento (briefing → formulário). |
| **Pinia** | Gerenciador de estado do Vue 3 — equivalente ao Vuex/Redux. |
| **PostgreSQL Provider** | Implementação de `PacienteProviderInterface` para produção. Usa SQLAlchemy + asyncpg. |
| **Provider Pattern** | Padrão arquitetural que desacopla a lógica de negócio (controller) da fonte de dados (provider). Troca de fonte via `STRATEGY` no roteador sem alterar o controller. |
| **PyJWT** | Biblioteca Python para geração e validação de tokens JWT. |
| **Pydantic v2** | Biblioteca de validação de dados Python — usada para validar entrada nas rotas FastAPI. |
| **RBAC** | Role-Based Access Control — controle de acesso baseado em roles derivadas dos grupos do AD. |
| **Soft Delete** | Exclusão lógica via campo `deleted_at`. Registros nunca são fisicamente deletados do banco. |
| **SQLAlchemy** | ORM Python — mapeamento objeto-relacional para PostgreSQL e SQLite. |
| **Tailwind CSS** | Framework CSS utilitário. Versão 4 no frontend. |
| **Vue 3** | Framework JavaScript progressivo para construção de interfaces. |
| **Vite** | Build tool para o frontend Vue. |
| **Zod** | Biblioteca de validação de schema TypeScript usada no frontend com Vee-validate. |

---

## 3. Status e Enumerações do Sistema

### Status de Fila
`Agendado` → `Aguardando` → `Em Atendimento` → `Pendente` → `Finalizado`

### Tipos de Entrada
`Retorno` | `Egresso` | `Encaminhamento Externo` | `Internação`

### Status de Marco
`confirmed` | `not-evaluated` | `not-achieved`

### Status de Sistema (Exame Físico)
`normal` | `alterado` | `nao-avaliado`

### Prioridade de Encaminhamento
`Eletivo` | `Prioritário` | `Urgente`

### Categoria de Alerta
`peso` | `marco` | `encaminhamento` | `falta` | `negligencia`

### Tipo de Alerta
`critico` | `atencao`

### Tendência de Peso
`up` | `down` | `stable`

---

## 4. Referências

- Normas do CFM (Conselho Federal de Medicina) sobre prontuário eletrônico.
- LGPD — Lei 13.709/2018.
- M-CHAT-R/F — Robins et al., 2014. Tradução e validação para o português brasileiro.
- Tabelas de percentil OMS (Organização Mundial da Saúde) para crescimento infantil.
- Manual do AGHU — documentação interna HC/UFPE.
- Manuais internos da ANS e CFM aplicáveis.
