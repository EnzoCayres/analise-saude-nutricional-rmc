-- Q4. Como a oferta de UBS se distribui entre os municipios, em relacao ao tamanho da populacao?
SELECT
    RANK() OVER (ORDER BY ubs_por_100mil_hab DESC) AS posicao,
    nome,
    populacao_total,
    n_ubs,
    ROUND(ubs_por_100mil_hab, 1)            AS ubs_por_100mil_hab,
    ROUND(1.0 * populacao_total / n_ubs, 0) AS habitantes_por_ubs,
    ROUND(1.0 * total_avaliados / n_ubs, 0) AS avaliados_sisvan_por_ubs
FROM v_indicadores
ORDER BY ubs_por_100mil_hab DESC;
