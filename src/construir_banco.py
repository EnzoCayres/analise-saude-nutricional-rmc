"""Constroi o banco SQLite a partir dos CSVs em dados/brutos.

Uso: python src/construir_banco.py
Saida: dados/processados/saude_nutricional_rmc.db
"""
import math
import sqlite3
import statistics
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
BANCO = RAIZ / "dados" / "processados" / "saude_nutricional_rmc.db"

# Nome oficial (com acento) de cada municipio. A ligacao entre as bases e feita pelo
# codigo do IBGE, porque os nomes aparecem com e sem acento conforme a fonte.
NOMES = {
    "350160": "Americana", "350380": "Artur Nogueira", "350950": "Campinas",
    "351280": "Cosmópolis", "351515": "Engenheiro Coelho", "351905": "Holambra",
    "351907": "Hortolândia", "352050": "Indaiatuba", "352340": "Itatiba",
    "352470": "Jaguariúna", "353180": "Monte Mor", "353200": "Morungaba",
    "353340": "Nova Odessa", "353650": "Paulínia", "353710": "Pedreira",
    "354580": "Santa Bárbara d'Oeste", "354800": "Santo Antônio de Posse",
    "355240": "Sumaré", "355620": "Valinhos", "355670": "Vinhedo",
}

# Uma UBS a mais de 30 km da mediana das UBS do proprio municipio tem coordenada
# provavelmente errada no cadastro e fica fora do mapa.
LIMITE_KM_COORDENADA = 30


def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia em km entre dois pontos (formula de haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def ler(nome_arquivo, **kwargs):
    return pd.read_csv(BRUTOS / nome_arquivo, dtype={"codigo_ibge": str, "municipio_id": str}, **kwargs)


def validar(pop, sisvan, socio, ubs):
    esperados = set(NOMES)
    for nome, df in [("populacao", pop), ("sisvan", sisvan), ("socioeconomico", socio)]:
        assert set(df["codigo_ibge"]) == esperados, f"{nome}: municipios diferentes do esperado"
        assert df["codigo_ibge"].is_unique, f"{nome}: codigo repetido"
    assert set(ubs["municipio_id"]) <= esperados, "UBS com municipio desconhecido"
    assert ubs["cnes_id"].is_unique, "UBS repetida"
    categorias = ["baixo_peso", "eutrofia", "sobrepeso", "obesidade_grau_1",
                  "obesidade_grau_2", "obesidade_grau_3"]
    assert (sisvan[categorias].sum(axis=1) == sisvan["total_avaliados"]).all(), "SISVAN: soma das categorias difere do total"


def marcar_coordenadas(ubs):
    """Adiciona a coluna coordenada_valida (1 ou 0) conforme a distancia da mediana municipal."""
    valida = pd.Series(1, index=ubs.index)
    for _, grupo in ubs.groupby("municipio_id"):
        lat_med = statistics.median(grupo["latitude"])
        lon_med = statistics.median(grupo["longitude"])
        for i, linha in grupo.iterrows():
            if distancia_km(lat_med, lon_med, linha["latitude"], linha["longitude"]) > LIMITE_KM_COORDENADA:
                valida[i] = 0
    return ubs.assign(coordenada_valida=valida)


def main():
    pop = ler("ibge_populacao_censo2022.csv")
    sisvan = ler("sisvan_imc_adultos.csv")
    socio = ler("ibge_socioeconomico.csv")
    ubs = ler("cnes_ubs.csv")
    validar(pop, sisvan, socio, ubs)
    ubs = marcar_coordenadas(ubs.rename(columns={"municipio_id": "municipio_id"}))

    BANCO.parent.mkdir(parents=True, exist_ok=True)
    if BANCO.exists():
        BANCO.unlink()
    con = sqlite3.connect(BANCO)
    con.executescript((RAIZ / "sql" / "01_schema.sql").read_text(encoding="utf-8"))

    municipio = pop[["codigo_ibge", "populacao_total", "populacao_20_a_59"]].copy()
    municipio.insert(1, "nome", municipio["codigo_ibge"].map(NOMES))
    municipio.to_sql("municipio", con, if_exists="append", index=False)
    sisvan.drop(columns=["municipio"]).to_sql("sisvan_imc", con, if_exists="append", index=False)
    socio.drop(columns=["municipio"]).to_sql("socioeconomico", con, if_exists="append", index=False)
    (ubs.rename(columns={"municipio_id": "codigo_ibge"})
        [["cnes_id", "codigo_ibge", "latitude", "longitude", "coordenada_valida"]]
        .to_sql("ubs", con, if_exists="append", index=False))
    con.commit()

    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ["municipio", "sisvan_imc", "socioeconomico", "ubs"]}
    descartadas = con.execute("SELECT COUNT(*) FROM ubs WHERE coordenada_valida = 0").fetchone()[0]
    con.close()
    print(f"Banco criado em {BANCO.relative_to(RAIZ)}")
    print("Linhas por tabela:", n)
    print(f"UBS com coordenada descartada: {descartadas}")


if __name__ == "__main__":
    main()
