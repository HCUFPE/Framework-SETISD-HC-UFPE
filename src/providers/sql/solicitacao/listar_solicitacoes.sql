-- Lista uma página de solicitações, da mais recente para a mais antiga (RN-01: somente leitura).
-- Filtra as solicitações pelos laboratórios e status, e traz todas as amostras das escolhidas.
-- TODO: confirmar com a TI do hospital o schema da view e os tipos das colunas.
-- TODO: a ordenação supõe data_solicitacao do tipo date. Se for texto em DD/MM/AAAA, usar TO_DATE.
WITH selecionadas AS (
    SELECT
        codigo_solicitacao,
        MAX(data_solicitacao) AS data_ordem
    FROM
        vw_solicitacao
    WHERE
        CAST(codigo_lab AS TEXT) = ANY(:codigos_lab)
        AND (NOT :filtrar_status OR cod_status_item = ANY(:codigos_status))
    GROUP BY
        codigo_solicitacao
    ORDER BY
        data_ordem DESC,
        codigo_solicitacao DESC
    LIMIT :limite
    OFFSET :deslocamento
)
SELECT
    v.codigo_solicitacao,
    v.numero_amostra,
    v.cod_status_item,
    v.status_item_exame,
    v.data_solicitacao,
    v.nome_paciente,
    v.data_nascimento,
    v.prontuario,
    v.especialidade,
    v.convenio,
    v.origem,
    v.unidade,
    v.codigo_lab,
    v.informacoes_clinica,
    v.sigla_exame,
    v.nome_exame,
    v.descricao_material
FROM
    vw_solicitacao v
    JOIN selecionadas s ON s.codigo_solicitacao = v.codigo_solicitacao
ORDER BY
    s.data_ordem DESC,
    v.codigo_solicitacao DESC,
    v.numero_amostra;
