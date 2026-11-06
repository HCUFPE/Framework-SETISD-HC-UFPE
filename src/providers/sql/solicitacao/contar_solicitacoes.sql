-- Conta as solicitações que entram na lista da Recepção (RN-01: somente leitura).
-- TODO: confirmar com a TI do hospital o schema da view e os tipos das colunas.
SELECT
    COUNT(DISTINCT codigo_solicitacao) AS total
FROM
    vw_solicitacao
WHERE
    CAST(codigo_lab AS TEXT) = ANY(:codigos_lab)
    AND (NOT :filtrar_status OR cod_status_item = ANY(:codigos_status));
