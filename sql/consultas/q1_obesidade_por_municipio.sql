-- Q1. Qual a proporcao de obesidade e de excesso de peso entre os adultos avaliados em cada municipio?
SELECT
    RANK() OVER (ORDER BY obesidade_pct DESC)  AS posicao,
    nome,
    total_avaliados,
    obesos,
    ROUND(obesidade_pct, 1)     AS obesidade_pct,
    ROUND(excesso_peso_pct, 1)  AS excesso_peso_pct,
    ROUND(baixo_peso_pct, 1)    AS baixo_peso_pct
FROM v_indicadores
ORDER BY obesidade_pct DESC;
