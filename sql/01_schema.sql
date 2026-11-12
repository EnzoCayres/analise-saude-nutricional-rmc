-- Esquema do banco SQLite do projeto.
-- Todas as tabelas se ligam pelo codigo_ibge (6 digitos), nunca pelo nome do municipio.

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_indicadores;
DROP TABLE IF EXISTS ubs;
DROP TABLE IF EXISTS socioeconomico;
DROP TABLE IF EXISTS sisvan_imc;
DROP TABLE IF EXISTS municipio;

CREATE TABLE municipio (
    codigo_ibge        TEXT PRIMARY KEY,
    nome               TEXT    NOT NULL,
    populacao_total    INTEGER NOT NULL CHECK (populacao_total > 0),
    populacao_20_a_59  INTEGER NOT NULL CHECK (populacao_20_a_59 > 0)
);

-- Estado nutricional de adultos atendidos no SUS (SISVAN), contagem por categoria de IMC.
CREATE TABLE sisvan_imc (
    codigo_ibge       TEXT PRIMARY KEY REFERENCES municipio (codigo_ibge),
    baixo_peso        INTEGER NOT NULL,
    eutrofia          INTEGER NOT NULL,
    sobrepeso         INTEGER NOT NULL,
    obesidade_grau_1  INTEGER NOT NULL,
    obesidade_grau_2  INTEGER NOT NULL,
    obesidade_grau_3  INTEGER NOT NULL,
    total_avaliados   INTEGER NOT NULL,
    CHECK (baixo_peso + eutrofia + sobrepeso + obesidade_grau_1
           + obesidade_grau_2 + obesidade_grau_3 = total_avaliados)
);

CREATE TABLE socioeconomico (
    codigo_ibge                       TEXT PRIMARY KEY REFERENCES municipio (codigo_ibge),
    renda_domiciliar_per_capita_2010  REAL NOT NULL,
    gini_2010                         REAL NOT NULL CHECK (gini_2010 BETWEEN 0 AND 1),
    pib_per_capita_2023               REAL NOT NULL
);

-- Unidades Basicas de Saude ativas (CNES, tipo de unidade 02).
CREATE TABLE ubs (
    cnes_id            INTEGER PRIMARY KEY,
    codigo_ibge        TEXT    NOT NULL REFERENCES municipio (codigo_ibge),
    latitude           REAL    NOT NULL,
    longitude          REAL    NOT NULL,
    coordenada_valida  INTEGER NOT NULL DEFAULT 1 CHECK (coordenada_valida IN (0, 1))
);

CREATE INDEX idx_ubs_municipio ON ubs (codigo_ibge);

-- Uma linha por municipio, com os indicadores usados nas consultas.
CREATE VIEW v_indicadores AS
SELECT
    m.codigo_ibge,
    m.nome,
    m.populacao_total,
    m.populacao_20_a_59,
    s.total_avaliados,
    100.0 * s.total_avaliados / m.populacao_20_a_59 AS cobertura_sisvan_pct,
    s.obesidade_grau_1 + s.obesidade_grau_2 + s.obesidade_grau_3 AS obesos,
    100.0 * (s.obesidade_grau_1 + s.obesidade_grau_2 + s.obesidade_grau_3)
          / s.total_avaliados AS obesidade_pct,
    100.0 * (s.sobrepeso + s.obesidade_grau_1 + s.obesidade_grau_2 + s.obesidade_grau_3)
          / s.total_avaliados AS excesso_peso_pct,
    100.0 * s.baixo_peso / s.total_avaliados AS baixo_peso_pct,
    e.renda_domiciliar_per_capita_2010 AS renda_2010,
    e.gini_2010,
    e.pib_per_capita_2023 AS pib_pc_2023,
    COALESCE(u.n_ubs, 0) AS n_ubs,
    100000.0 * COALESCE(u.n_ubs, 0) / m.populacao_total AS ubs_por_100mil_hab
FROM municipio m
JOIN sisvan_imc     s USING (codigo_ibge)
JOIN socioeconomico e USING (codigo_ibge)
LEFT JOIN (SELECT codigo_ibge, COUNT(*) AS n_ubs FROM ubs GROUP BY codigo_ibge) u
       USING (codigo_ibge);
