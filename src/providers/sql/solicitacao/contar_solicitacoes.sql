-- Conta as solicitações que entram na lista da Recepção, com os mesmos filtros da listagem (RN-01: somente leitura).
-- TODO: confirmar com a TI do hospital o schema da view e os tipos das colunas.
SELECT
    COUNT(*) AS total
FROM
    (
        SELECT
            codigo_solicitacao
        FROM
            vw_solicitacao
        WHERE
            CAST(codigo_lab AS TEXT) = ANY(:codigos_lab)
            AND (NOT :filtrar_status OR cod_status_item = ANY(:codigos_status))
            AND (CAST(:filtro_codigo AS TEXT) IS NULL
                OR STRPOS(CAST(codigo_solicitacao AS TEXT), CAST(:filtro_codigo AS TEXT)) > 0)
            AND (CAST(:filtro_data AS DATE) IS NULL OR data_solicitacao = CAST(:filtro_data AS DATE))
            AND (CAST(:filtro_paciente AS TEXT) IS NULL
                OR STRPOS(LOWER(COALESCE(nome_paciente, '')), LOWER(CAST(:filtro_paciente AS TEXT))) > 0)
            AND (CAST(:filtro_prontuario AS TEXT) IS NULL
                OR STRPOS(LOWER(COALESCE(CAST(prontuario AS TEXT), '')), LOWER(CAST(:filtro_prontuario AS TEXT))) > 0)
            AND (CAST(:filtro_origem AS TEXT) IS NULL
                OR STRPOS(LOWER(COALESCE(origem, '')), LOWER(CAST(:filtro_origem AS TEXT))) > 0)
            AND (CAST(:filtro_clinica AS TEXT) IS NULL
                OR STRPOS(
                    LOWER(COALESCE(especialidade, '') || ' ' || COALESCE(unidade, '')),
                    LOWER(CAST(:filtro_clinica AS TEXT))
                ) > 0)
        GROUP BY
            codigo_solicitacao
        HAVING
            (NOT :filtrar_bancada OR BOOL_OR(CAST(codigo_lab AS TEXT) = ANY(:codigos_lab_filtro)))
    ) AS contadas;
    