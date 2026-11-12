-- Q6. As coordenadas das UBS no CNES sao confiaveis para um mapa?
-- Conta, por municipio, quantas UBS foram descartadas por ficarem longe demais do conjunto
-- e quantas dividem exatamente a mesma coordenada com outra unidade.
WITH repetidas AS (
    SELECT latitude, longitude, COUNT(*) AS qtd
    FROM ubs
    GROUP BY latitude, longitude
    HAVING COUNT(*) > 1
)
SELECT
    m.nome,
    COUNT(*)                                                    AS ubs,
    SUM(CASE WHEN u.coordenada_valida = 0 THEN 1 ELSE 0 END)    AS coordenada_descartada,
    SUM(CASE WHEN r.qtd IS NOT NULL THEN 1 ELSE 0 END)          AS em_coordenada_repetida
FROM ubs u
JOIN municipio m USING (codigo_ibge)
LEFT JOIN repetidas r ON r.latitude = u.latitude AND r.longitude = u.longitude
GROUP BY m.nome
ORDER BY coordenada_descartada DESC, em_coordenada_repetida DESC, m.nome;
