-- Q5. Quais municipios combinam obesidade acima da mediana da regiao e oferta de UBS abaixo
-- da mediana? E um recorte exploratorio para priorizar a investigacao, nao um diagnostico.
WITH ordenado AS (
    SELECT
        obesidade_pct,
        ubs_por_100mil_hab,
        ROW_NUMBER() OVER (ORDER BY obesidade_pct)       AS rn_ob,
        ROW_NUMBER() OVER (ORDER BY ubs_por_100mil_hab)  AS rn_ubs,
        COUNT(*) OVER ()                                 AS n
    FROM v_indicadores
),
medianas AS (
    SELECT
        (SELECT AVG(obesidade_pct)      FROM ordenado WHERE rn_ob  IN ((n + 1) / 2, (n + 2) / 2)) AS med_obesidade,
        (SELECT AVG(ubs_por_100mil_hab) FROM ordenado WHERE rn_ubs IN ((n + 1) / 2, (n + 2) / 2)) AS med_ubs
    FROM ordenado
    LIMIT 1
)
SELECT
    v.nome,
    ROUND(v.obesidade_pct, 1)       AS obesidade_pct,
    ROUND(v.ubs_por_100mil_hab, 1)  AS ubs_por_100mil_hab,
    ROUND(v.cobertura_sisvan_pct, 1) AS cobertura_sisvan_pct,
    CASE
        WHEN v.obesidade_pct >  m.med_obesidade AND v.ubs_por_100mil_hab <  m.med_ubs THEN 'obesidade alta, UBS baixa'
        WHEN v.obesidade_pct >  m.med_obesidade AND v.ubs_por_100mil_hab >= m.med_ubs THEN 'obesidade alta, UBS alta'
        WHEN v.obesidade_pct <= m.med_obesidade AND v.ubs_por_100mil_hab <  m.med_ubs THEN 'obesidade baixa, UBS baixa'
        ELSE                                                                               'obesidade baixa, UBS alta'
    END AS grupo
FROM v_indicadores v
CROSS JOIN medianas m
ORDER BY grupo, v.obesidade_pct DESC;
