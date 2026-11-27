-- Consulta auxiliar de solicitações de exames no AGHU por parte do nome do paciente (busca ativa)
SELECT
    pac.prontuario AS prontuario,
    pac.nome AS nome,
    CAST(NULL AS VARCHAR) AS telefone,
    CAST(NULL AS VARCHAR) AS cidade,
    CAST(NULL AS VARCHAR) AS estado,
    soe.seq AS codigo_solicitacao,
    soe.criado_em AS data_solicitao,
    unf.descricao AS unidade_solicitante,
    ise.ufe_ema_exa_sigla AS codigo_exame,
    exa.descricao AS nome_exame,
    pes.codigo AS id_funcionario,
    pes.nome AS nome_funcionario
FROM
    agh.ael_solicitacao_exames soe
    INNER JOIN agh.ael_item_solicitacao_exames ise
        ON ise.soe_seq = soe.seq
    INNER JOIN agh.ael_exames exa
        ON exa.sigla = ise.ufe_ema_exa_sigla
    LEFT JOIN agh.agh_atendimentos atd
        ON atd.seq = soe.atd_seq
    LEFT JOIN agh.aip_pacientes pac
        ON pac.codigo = atd.pac_codigo
    LEFT JOIN agh.agh_unidades_funcionais unf
        ON unf.seq = soe.unf_seq
    LEFT JOIN agh.rap_servidores ser
        ON ser.matricula = soe.ser_matricula
        AND ser.vin_codigo = soe.ser_vin_codigo
    LEFT JOIN agh.rap_pessoas_fisicas pes
        ON pes.codigo = ser.pes_codigo
WHERE
    pac.nome ILIKE #nome
ORDER BY
    pac.nome,
    soe.criado_em DESC
LIMIT 200;
