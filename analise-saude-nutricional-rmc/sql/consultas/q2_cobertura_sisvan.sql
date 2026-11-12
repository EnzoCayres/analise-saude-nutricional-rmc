-- Q2. Quanto da populacao adulta (20 a 59 anos) o SISVAN realmente alcanca em cada municipio?
-- Cobertura baixa significa que a proporcao de obesidade descreve pouca gente e pode nao
-- representar o municipio.
SELECT
    nome,
    populacao_20_a_59,
    total_avaliados,
    ROUND(cobertura_sisvan_pct, 1) AS cobertura_pct,
    CASE
        WHEN cobertura_sisvan_pct < 5  THEN 'baixa (menos de 5%)'
        WHEN cobertura_sisvan_pct < 15 THEN 'media (5% a 15%)'
        ELSE                                'alta (15% ou mais)'
    END AS faixa_cobertura
FROM v_indicadores
ORDER BY cobertura_sisvan_pct;
