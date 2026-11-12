-- Q3. A obesidade entre os avaliados varia junto com renda, desigualdade e PIB per capita?
-- A consulta entrega a tabela de analise. As correlacoes de Spearman sao calculadas em
-- src/analise.py, porque o SQLite nao tem funcao de correlacao.
SELECT
    nome,
    ROUND(obesidade_pct, 2)      AS obesidade_pct,
    ROUND(excesso_peso_pct, 2)   AS excesso_peso_pct,
    ROUND(renda_2010, 2)         AS renda_2010,
    gini_2010,
    ROUND(pib_pc_2023, 2)        AS pib_pc_2023,
    ROUND(cobertura_sisvan_pct, 1) AS cobertura_pct
FROM v_indicadores
ORDER BY obesidade_pct DESC;
