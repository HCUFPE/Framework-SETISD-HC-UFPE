# Glossário e Referências

## 1. Termos do Domínio Hospitalar e da Central de Marcação

* **AGHU:** Aplicação de Gestão para Hospitais Universitários — sistema oficial mantido pela sede da EBSERH em Brasília. Nosso sistema acessa sua base apenas em modo **somente leitura**.
* **EBSERH:** Empresa Brasileira de Serviços Hospitalares, gestora do HC-UFPE.
* **HC-UFPE:** Hospital das Clínicas da Universidade Federal de Pernambuco.
* **SETISD:** Setor de Tecnologia da Informação e Saúde Digital do HC-UFPE.
* **Central de Marcação:** Setor interno responsável por organizar a fila, contatar pacientes, confirmar disponibilidade e efetivar o agendamento de exames ambulatoriais no AGHU.
* **Prontuário:** Número identificador principal do paciente no HC-UFPE (ex: `2159478/3`). Priorizado como chave em relação ao CPF, pois há pacientes sem CPF cadastrado.
* **Número da Solicitação (`codigo_solicitacao` / `soe.seq`):** Código único gerado no AGHU quando o médico solicita um ou mais exames em uma consulta ambulatorial.
* **Ticket de Solicitação (`AELR_TICKET_PACIENTE`):** Comprovante impresso emitido pelo AGHU e entregue ao paciente na consulta (não pode ser modificado pelo sistema satélite).
* **Unidade Solicitante / Clínica Solicitante:** Setor ou especialidade médica que originou o pedido de exame (ex: Oncologia, Nefrologia, Cardiologia, Pediatria).
* **Unidade Executora / UDI:** Setor que executa o exame (ex: *UDI — Unidade de Diagnóstico por Imagem*: Ultrassonografia, Mamografia, Densitometria Óssea, Medicina Nuclear).
* **Grade de Agendamento:** Agenda específica de horários disponíveis de um profissional/equipamento em determinada unidade executora (ex: médico que realiza apenas ultrassom mamária).
* **Higienização (`Forms × AGHU`):** Etapa automatizada que cruza a planilha preenchida pelos pacientes no Google Forms com os registros oficiais do AGHU para filtrar erros de digitação, exames divergentes, solicitações duplicadas e exames já realizados.
* **Janela de Retorno:** Prazo máximo ou intervalo obrigatório entre a realização do exame e a data da consulta de retorno do paciente (ex: Espirometria até 10 dias antes; INR até 72h).
* **Prazo de 24 horas (Confirmação):** Tempo limite dado ao paciente após o contato via WhatsApp para confirmar disponibilidade antes da marcação definitiva no AGHU (alinhamento de 06/11); vencido o prazo sem resposta, a vaga segue para o próximo da fila.
* **TFD (Tratamento Fora de Domicílio):** Programa de transporte público diário que traz pacientes de municípios do interior até o HC-UFPE.
* **RMR:** Região Metropolitana do Recife (usada junto à Capital e Interior no **filtro geográfico operacional** para vagas urgentes de última hora).
* **CMCE:** Central de Marcação de Consultas e Exames do Estado (regulação externa do SUS — **fora de escopo** deste sistema).

## 2. Termos Técnicos do Framework

* **AD / LDAP (`EBSERHNET`):** Active Directory corporativo utilizado na Etapa 1 da autenticação.
* **RBAC:** *Role-Based Access Control* — controle de autorização por perfis armazenados localmente no banco da aplicação.
* **Padrão Provider + Strategy:** Camada de acesso a dados desacoplada que permite alternar entre leitura de `CSV` (dev offline) e `PostgreSQL` (produção AGHU) alterando uma única estratégia no roteador.
* **Default-Private Router Pattern:** Regra arquitetural que exige autenticação declarada no construtor de todo `APIRouter` de domínio clínico.
* **SDD / CARE:** *Spec-Driven Development* usando o formato *Context, Action, Result, Evaluation* para requisitos e casos de uso testáveis.
* **SemVer:** Versionamento Semântico (`vMAJOR.MINOR.PATCH`).

## 3. Referências

* Documentação oficial do [`Framework-SETISD-HC-UFPE`](../../README.md) e [`AGENTS.md`](../../AGENTS.md).
* Artefatos da pasta compartilhada **Exames 2026.2** (SETISD / HC-UFPE): *Resumo do Escopo*, consulta SQL oficial (`consulta_aghu_exames.sql`), CSV anonimizado, exemplo de Ticket (`AELR_TICKET_PACIENTE`) e atas de validação com SETISD e Central de Marcação (25/09 a 10/11/2026).
* Lei Geral de Proteção de Dados Pessoais (LGPD — Lei nº 13.709/2018).
