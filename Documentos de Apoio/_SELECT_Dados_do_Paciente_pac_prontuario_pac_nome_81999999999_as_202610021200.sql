SELECT 
    -- Dados do Paciente
    pac.prontuario,
    pac.nome,
	'81999999999' as telefone,
	'Recife' as cidade,
	'Pernambuco' as Estado,
    
    -- Dados da Solicitação
    soe.seq AS codigo_solicitacao,
    soe.criado_em AS data_solicitao,
    unf_s.descricao AS unidade_solicitante,
    
    -- Dados do Exame
    ise.ufe_ema_exa_sigla AS codigo_exame,
    exa.descricao AS nome_exame,
    
    -- Dados do Funcionário (Solicitante)
    pes_s.codigo AS id_funcionario,
    pes_s.nome AS nome_funcionario

FROM agh.ael_solicitacao_exames soe
    -- Ligações para Exame
    JOIN agh.ael_item_solicitacao_exames ise ON ise.soe_seq = soe.seq
    LEFT JOIN agh.ael_exames exa ON exa.sigla::text = ise.ufe_ema_exa_sigla::text
    
    -- Ligações para Unidade Solicitante
    LEFT JOIN agh.agh_unidades_funcionais unf_s ON unf_s.seq = soe.unf_seq
    
    -- Ligações para Paciente
    LEFT JOIN agh.agh_atendimentos atd ON atd.seq = soe.atd_seq
    LEFT JOIN agh.aip_pacientes pac ON pac.codigo = atd.pac_codigo
    
    -- Ligações para Funcionário (Profissional Solicitante)
    LEFT JOIN agh.rap_servidores srv_s ON srv_s.matricula = soe.ser_matricula AND srv_s.vin_codigo = soe.ser_vin_codigo
    LEFT JOIN agh.rap_pessoas_fisicas pes_s ON pes_s.codigo = srv_s.pes_codigo
    WHERE unf_s.descricao LIKE 'UNIDADE DE DIAGNÓSTICO POR IMAGEM%' 
   	OR unf_s.descricao LIKE '%UDI%'
AND soe.criado_em >= CURRENT_DATE - INTERVAL '60 days'
