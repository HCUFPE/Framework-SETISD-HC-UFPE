# Documento de Visão

1. **Problema e Oportunidade**
O Problema: Alta carga operacional na bancada devido à redundância de processos (dupla assinatura no sistema e em livro físico), erros/inconsistências de dados cadastrais de amostras vindos da integração com o AGHU e fragmentação do controle de amostras em planilhas paralelas vulneráveis a falhas de preenchimento.
Impacto: Atraso no Turnaround Time (TAT) de biópsias e laudos histopatológicos, retrabalho frequente das equipes de recepção e bancada, risco de perda de rastreabilidade de amostras corporais e dificuldade da gestão em acompanhar gargalos de produção em tempo real por falta de indicadores unificados.
Solução Proposta: Implantação do Livro de Protocolo Eletrônico e Painel de Gestão do SAP, centralizando a rastreabilidade legal com assinatura eletrônica institucional, aplicando regras rígidas de validação na recepção e fornecendo visibilidade de SLA em tempo real por fase operacional.
---
2. **Partes Interessadas (Stakeholders)**
Usuários Finais: Médicos Patologistas, Residentes, Técnicos de Histologia/Anatomia Patológica, Recepcionistas do SAP.
Patrocinadores: Diretoria Médica/Hospitalar, Chefia do SAP, Gestão de TI / Sistemas de Informação.
Apoiadores & Auditores: Gestão da Qualidade / Acreditação Hospitalar, Equipe de Regulação, Equipe do AGHU, Setor Jurídico e Compliance.
Beneficiários Diretos Internos (Quem ganha no dia a dia):
Técnicos de Bancada e Recepcionistas do SAP: Eliminação do retrabalho manual, fim da dupla digitação (livro físico + sistema) e fim da necessidade de "caçar" informações de fichas incompletas vindas do AGHU.
Corpo Clínico (Médicos Patologistas e Residentes): Acesso a amostras melhor cadastradas, visibilidade clara dos prazos por fase e segurança jurídica completa nos laudos com a assinatura eletrônica oficial.
Chefia do SAP e Gestores da Qualidade: Controle total e centralizado da operação via painel de TAT (sem dependência de planilhas paralelas), facilidade em auditorias de acreditação (ONA/PALC) e garantia de auditabilidade no rito de retificação.
Equipe do AGHU e Regulação: Alinhamento imediato quando houver inconformidades na origem, forçando a melhoria contínua da qualidade do cadastro do paciente desde a solicitação.
Beneficiários Finais (Externos):
Pacientes: Diagnósticos mais rápidos (menor tempo de espera por laudos de biópsias), redução do risco de trocas de amostras e garantia de maior segurança no cuidado prestado.
Diretoria Hospitalar e Patrocinadores: Redução de custos operacionais com retrabalho, mitigações de riscos jurídicos/sanitários e aumento da capacidade produtiva e reputação da instituição.
---
3. **Escopo do Produto**
O que ESTÁ no Escopo (Dentro do Projeto):
Módulo de Protocolo Eletrônico: Livro digital com validade jurídica, rastreabilidade completa de entradas/saídas e rito de retificação/auditoria (versionamento com justificativa obrigatória e log).
Validação de Entrada (Integração AGHU - RN-04): Trava automática na recepção para requisições com dados incompletos/inconsistentes, com emissão de alerta automático para o setor solicitante no AGHU.
Painel de Controle e Gestão visual de SLAs: Monitoramento em tempo real do tempo de permanência da amostra em cada fase (Macroscopia, Processamento, Microscopia e Laudo) com alertas visuais de atraso (Turnaround Time - TAT).
Descontinuação da Planilha Paralela (RN-07): Migração total dos controles operacionais para o sistema no momento do go-live.
O que NÃO ESTÁ no Escopo (Fora do Projeto):
Alterações no código-fonte interno do AGHU (o projeto apenas consome e valida as APIs/integrações do AGHU).
Aquisição ou manutenção de hardware de bancada (impressoras térmicas, microtótomos, leitores de código de barras).
Módulo de faturamento hospitalar/tabelas SUS (gerenciado exclusivamente pelos módulos nativos do AGHU).
---
4. **Metas e Objetivos de Negócio**
Redução do Turnaround Time (TAT): Reduzir em 25% o tempo médio total entre a recepção da amostra e a liberação do laudo final em até 90 dias após o go-live.
Eliminação do Erro na Origem: Reduzir a zero o ingresso de amostras com dados cadastrais incorruptos ou incompletos na bancada através da trava na recepção.
Ganho de Produtividade Operacional: Eliminar 100% do tempo gasto com preenchimento manual em livros físicos e planilhas paralelas.
Conformidade para Acreditação (Qualidade): Atingir 100% de auditabilidade nos registros do SAP, cumprindo integralmente os requisitos de rastreabilidade de órgãos acreditadores (ex.: ONA, PALC).
