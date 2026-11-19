-- Lista uma página de solicitações (RN-01: somente leitura).
-- Filtra pelos laboratórios, pelo status e pelos filtros por coluna da tela, e traz todas as amostras das escolhidas.
-- Ordem: sem ordenação pedida, as prioritárias primeiro e depois da mais recente para a mais antiga.
-- Prioritária: tem amostra de laboratório urgente (CO) e não está entre as já recebidas.
-- Com :ordenar_por, a coluna escolhida (e a direção) vale no lugar da prioridade; empates seguem por data.
-- TODO: confirmar com a TI do hospital o schema da view e os tipos das colunas.
-- TODO: a ordenação supõe data_solicitacao do tipo date. Se for texto em DD/MM/AAAA, usar TO_DATE.
WITH agrupadas AS (
    SELECT
        codigo_solicitacao,
        MAX(data_solicitacao) AS data_ordem,
        MAX(
            CASE
                WHEN CAST(codigo_lab AS TEXT) = ANY(:codigos_lab_urgentes)
                    AND NOT (CAST(codigo_solicitacao AS TEXT) = ANY(:codigos_excluidas))
                THEN 1 ELSE 0
            END
        ) AS prioridade,
        CASE CAST(:ordenar_por AS TEXT)
            WHEN 'paciente' THEN MIN(LOWER(COALESCE(nome_paciente, '')))
            WHEN 'prontuario' THEN MIN(LOWER(COALESCE(CAST(prontuario AS TEXT), '')))
            WHEN 'origem' THEN MIN(LOWER(COALESCE(origem, '')))
            WHEN 'clinica' THEN MIN(LOWER(COALESCE(especialidade, '') || ' ' || COALESCE(unidade, '')))
        END AS chave_texto
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
),
ordenadas AS (
    SELECT
        a.*,
        ROW_NUMBER() OVER (
            ORDER BY
                a.prioridade DESC,
                CASE WHEN CAST(:direcao AS TEXT) = 'asc' THEN a.chave_texto END ASC,
                CASE WHEN CAST(:direcao AS TEXT) = 'desc' THEN a.chave_texto END DESC,
                CASE WHEN CAST(:ordenar_por AS TEXT) = 'data' AND CAST(:direcao AS TEXT) = 'asc'
                    THEN COALESCE(a.data_ordem, DATE '0001-01-01') END ASC,
                CASE WHEN CAST(:ordenar_por AS TEXT) = 'data' AND CAST(:direcao AS TEXT) = 'desc'
                    THEN COALESCE(a.data_ordem, DATE '0001-01-01') END DESC,
                CASE WHEN CAST(:ordenar_por AS TEXT) = 'codigo' AND CAST(:direcao AS TEXT) = 'asc'
                    THEN a.codigo_solicitacao END ASC,
                CASE WHEN CAST(:ordenar_por AS TEXT) = 'codigo' AND CAST(:direcao AS TEXT) = 'desc'
                    THEN a.codigo_solicitacao END DESC,
                a.data_ordem DESC,
                a.codigo_solicitacao DESC
        ) AS posicao
    FROM
        agrupadas a
),
selecionadas AS (
    SELECT
        *
    FROM
        ordenadas
    ORDER BY
        posicao
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
    s.posicao,
    v.numero_amostra;
    