-- Consulta de LEITURA da solicitação e de suas amostras no AGHU (RN-01: somente leitura).
-- Uma linha por amostra. Colunas: ver "Layout da vw_solicitacao" em docs/especificacao/05-interfaces.md.
-- TODO: confirmar com a TI do hospital o schema da view e a permissão de leitura.
-- TODO: confirmar os tipos. O CSV exportado traz codigo_solicitacao como inteiro e as datas
--       em DD/MM/AAAA; o provider aceita tipo date ou esse formato de texto.
-- TODO: confirmar se a view já vem filtrada para os 5 laboratórios, como o CSV exportado.
SELECT
    codigo_solicitacao,
    numero_amostra,
    cod_status_item,
    status_item_exame,
    data_solicitacao,
    nome_paciente,
    data_nascimento,
    prontuario,
    especialidade,
    convenio,
    origem,
    unidade,
    codigo_lab,
    informacoes_clinica,
    sigla_exame,
    nome_exame,
    descricao_material
FROM
    vw_solicitacao
WHERE
    CAST(codigo_solicitacao AS TEXT) = :codigo
ORDER BY
    numero_amostra;
