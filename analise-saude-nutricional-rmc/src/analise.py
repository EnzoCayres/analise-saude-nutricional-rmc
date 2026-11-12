"""Roda as consultas SQL, calcula as estatisticas e gera os graficos.

Uso (depois de python src/construir_banco.py):
    python src/analise.py
Saidas: resultados/*.csv e graficos/*.png
"""
import math
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "processados" / "saude_nutricional_rmc.db"
CONSULTAS = RAIZ / "sql" / "consultas"
GRAFICOS = RAIZ / "graficos"
RESULTADOS = RAIZ / "resultados"

COBERTURA_MINIMA = 5.0  # abaixo disso a proporcao de obesidade e pouco confiavel

# Cores: tons neutros para contexto, azul para a serie principal, laranja para destaque.
SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#e6e5e1"
AZUL = "#2a78d6"
LARANJA = "#eb6834"
CINZA = "#9b9a94"

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
    "axes.edgecolor": GRADE, "axes.labelcolor": TEXTO_2, "xtick.color": TEXTO_2, "ytick.color": TEXTO_2,
    "text.color": TEXTO, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def consulta(con, arquivo):
    return pd.read_sql_query((CONSULTAS / arquivo).read_text(encoding="utf-8"), con)


def wilson(sucessos, n, z=1.96):
    """Intervalo de confianca de 95% (Wilson) para uma proporcao, em pontos percentuais."""
    p = sucessos / n
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    meia = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return 100 * (centro - meia), 100 * (centro + meia)


def salvar(fig, nome):
    GRAFICOS.mkdir(exist_ok=True)
    fig.savefig(GRAFICOS / nome, dpi=150, bbox_inches="tight")
    plt.close(fig)


DESLOC_COBERTURA = {"Sumaré": (0, -13, "center"), "Vinhedo": (-5, -9, "right"), "Indaiatuba": (-3, 9, "right"),
                    "Campinas": (6, 8, "left"), "Nova Odessa": (-5, -18, "right"), "Monte Mor": (7, -3, "left")}
DESLOC_QUADRANTE = {"Nova Odessa": (-5, 5, "right"), "Vinhedo": (-5, -8, "right"), "Paulínia": (6, 4, "left"),
                    "Sumaré": (6, -3, "left"), "Indaiatuba": (-6, -3, "right"), "Campinas": (6, -8, "left")}
DESLOC_MAPA = {"Americana": (0, 12, "center"), "Santa Bárbara d'Oeste": (-26, -16, "center"), "Sumaré": (8, -14, "left"),
               "Hortolândia": (-6, -17, "center"), "Nova Odessa": (12, -16, "left")}


def rotular(ax, x, y, nome, deslocs, fonte=8, cor=TEXTO_2):
    dx, dy, ha = deslocs.get(nome, (5, 3, "left"))
    ax.annotate(curto(nome), (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, fontsize=fonte, color=cor)


def curto(nome):
    return {"Santa Bárbara d'Oeste": "Sta. Bárbara d'Oeste", "Santo Antônio de Posse": "Sto. Antônio de Posse",
            "Engenheiro Coelho": "Eng. Coelho"}.get(nome, nome)


# ---------------------------------------------------------------- graficos

def grafico_obesidade(d):
    d = d.sort_values("obesidade_pct")
    ic = [wilson(o, n) for o, n in zip(d["obesos"], d["total_avaliados"])]
    baixo = d["cobertura_sisvan_pct"] < COBERTURA_MINIMA
    fig, ax = plt.subplots(figsize=(8, 7))
    y = np.arange(len(d))
    for yi, (v, (lo, hi), b) in enumerate(zip(d["obesidade_pct"], ic, baixo)):
        ax.barh(yi, v, height=0.62, color=SUPERFICIE if b else AZUL, edgecolor=CINZA if b else AZUL,
                hatch="////" if b else None, linewidth=1.2)
        ax.plot([lo, hi], [yi, yi], color=TEXTO, linewidth=1.3, zorder=4)
        ax.text(hi + 0.6, yi, f"{v:.1f}%", va="center", fontsize=9, color=TEXTO)
    ax.set_yticks(y, [curto(n) for n in d["nome"]])
    ax.set_xlim(0, 62)
    ax.set_xlabel("Obesidade entre os adultos avaliados (%)  |  linha = intervalo de confiança de 95%")
    ax.set_title("Obesidade entre os adultos atendidos no SUS, por município")
    ax.grid(axis="y", visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=AZUL, edgecolor=AZUL, label="cobertura do SISVAN de 5% ou mais"),
                       Patch(facecolor=SUPERFICIE, edgecolor=CINZA, hatch="////", label="cobertura abaixo de 5% (pouco confiável)")],
              loc="upper center", bbox_to_anchor=(0.45, -0.1), ncol=2, frameon=False, fontsize=9)
    salvar(fig, "01_obesidade_por_municipio.png")


def grafico_cobertura(d):
    d = d.sort_values("cobertura_sisvan_pct")
    fig, ax = plt.subplots(figsize=(8, 7))
    y = np.arange(len(d))
    for yi, v in zip(y, d["cobertura_sisvan_pct"]):
        b = v < COBERTURA_MINIMA
        ax.barh(yi, v, height=0.62, color=SUPERFICIE if b else AZUL, edgecolor=CINZA if b else AZUL,
                hatch="////" if b else None, linewidth=1.2)
        ax.text(v + 0.5, yi, f"{v:.1f}%", va="center", fontsize=9)
    ax.axvline(COBERTURA_MINIMA, color=LARANJA, linewidth=1.4, linestyle="--")
    ax.text(COBERTURA_MINIMA + 0.4, -0.9, "limite de 5%", color=TEXTO_2, fontsize=9, va="center")
    ax.set_yticks(y, [curto(n) for n in d["nome"]])
    ax.set_xlim(0, 35)
    ax.set_ylim(-1.4, len(d) - 0.4)
    ax.set_xlabel("Adultos avaliados no SISVAN em relação à população de 20 a 59 anos (%)")
    ax.set_title("Quanto da população adulta o SISVAN alcança")
    ax.grid(axis="y", visible=False)
    salvar(fig, "02_cobertura_sisvan.png")


def dispersao(ax, d, x, y, xlabel, ylabel, log=False, rotulos=True, deslocs=None):
    baixo = d["cobertura_sisvan_pct"] < COBERTURA_MINIMA
    ax.scatter(d.loc[~baixo, x], d.loc[~baixo, y], s=46, color=AZUL, zorder=3)
    ax.scatter(d.loc[baixo, x], d.loc[baixo, y], s=46, facecolor=SUPERFICIE, edgecolor=CINZA, linewidth=1.5, zorder=3)
    if log:
        ax.set_xscale("log")
        marcas = [40000, 100000, 200000, 600000]
        ax.set_xticks(marcas)
        ax.set_xticklabels([f"{m // 1000} mil" for m in marcas])
        ax.minorticks_off()
    if rotulos:
        for _, r in d.iterrows():
            rotular(ax, r[x], r[y], r["nome"], deslocs or {}, fonte=7.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def grafico_cobertura_vs_obesidade(d, rho, p):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    dispersao(ax, d, "cobertura_sisvan_pct", "obesidade_pct", "Cobertura do SISVAN (%)", "Obesidade entre os avaliados (%)", deslocs=DESLOC_COBERTURA)
    ax.set_title("Onde o SISVAN alcança menos gente, a obesidade medida é maior")
    ax.text(0.98, 0.96, f"Spearman ρ = {rho:.2f} (p = {p:.3f}, n = 20)", transform=ax.transAxes, ha="right", va="top", color=TEXTO_2)
    salvar(fig, "03_obesidade_vs_cobertura.png")


def grafico_socioeconomia(d, cor):
    fig, eixos = plt.subplots(1, 3, figsize=(14, 4.8), sharey=True)
    specs = [("renda_2010", "Renda domiciliar per capita, 2010 (R$)", False),
             ("gini_2010", "Índice de Gini, 2010", False),
             ("pib_pc_2023", "PIB per capita, 2023 (R$, escala log)", True)]
    for ax, (col, rotulo, log) in zip(eixos, specs):
        dispersao(ax, d, col, "obesidade_pct", rotulo, "Obesidade entre os avaliados (%)" if col == "renda_2010" else "", log=log, rotulos=False)
        r = cor[(cor["variavel"] == col) & (cor["amostra"] == "todos os municípios")].iloc[0]
        ax.set_title(f"ρ = {r['rho']:.2f}  (p = {r['p']:.2f})", fontsize=11)
    fig.suptitle("Obesidade e indicadores socioeconômicos (n = 20; círculos vazados: cobertura do SISVAN abaixo de 5%)",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.03)
    salvar(fig, "04_obesidade_vs_socioeconomia.png")


def grafico_ubs(d):
    d = d.sort_values("ubs_por_100mil_hab")
    fig, ax = plt.subplots(figsize=(8, 7))
    y = np.arange(len(d))
    ax.barh(y, d["ubs_por_100mil_hab"], height=0.62, color=AZUL)
    for yi, v, n in zip(y, d["ubs_por_100mil_hab"], d["n_ubs"]):
        ax.text(v + 0.5, yi, f"{v:.1f}  ({n} UBS)", va="center", fontsize=9)
    ax.set_yticks(y, [curto(n) for n in d["nome"]])
    ax.set_xlim(0, 46)
    ax.set_xlabel("UBS ativas por 100 mil habitantes (CNES; população do Censo 2022)")
    ax.set_title("Oferta de UBS em relação ao tamanho da população")
    ax.grid(axis="y", visible=False)
    salvar(fig, "05_ubs_por_100mil.png")


def grafico_quadrante(d):
    mo, mu = d["obesidade_pct"].median(), d["ubs_por_100mil_hab"].median()
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    alvo = (d["obesidade_pct"] > mo) & (d["ubs_por_100mil_hab"] < mu)
    baixo = d["cobertura_sisvan_pct"] < COBERTURA_MINIMA
    for mask, cor in [(~alvo, AZUL), (alvo, LARANJA)]:
        for vazado in (False, True):
            m = mask & (baixo == vazado)
            ax.scatter(d.loc[m, "obesidade_pct"], d.loc[m, "ubs_por_100mil_hab"], s=52, zorder=3,
                       facecolor=SUPERFICIE if vazado else cor, edgecolor=cor, linewidth=1.5)
    for _, r in d.iterrows():
        rotular(ax, r["obesidade_pct"], r["ubs_por_100mil_hab"], r["nome"], DESLOC_QUADRANTE)
    ax.axvline(mo, color=CINZA, linewidth=1, linestyle="--")
    ax.axhline(mu, color=CINZA, linewidth=1, linestyle="--")
    ax.set_xlabel(f"Obesidade entre os avaliados (%)  |  mediana: {mo:.1f}%\ncírculo vazado: cobertura do SISVAN abaixo de 5%")
    ax.set_ylabel(f"UBS por 100 mil habitantes  |  mediana: {mu:.1f}")
    ax.set_title("Obesidade acima da mediana com oferta de UBS abaixo da mediana (laranja)")
    salvar(fig, "06_quadrante_obesidade_ubs.png")


def grafico_mapa(con):
    u = pd.read_sql_query("SELECT u.latitude, u.longitude, m.nome FROM ubs u JOIN municipio m USING (codigo_ibge) WHERE u.coordenada_valida = 1", con)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(u["longitude"], u["latitude"], s=16, color=AZUL, alpha=0.8, linewidth=0, zorder=3)
    for nome, g in u.groupby("nome"):
        dx, dy, ha = DESLOC_MAPA.get(nome, (0, 9, "center"))
        ax.annotate(curto(nome), (g["longitude"].median(), g["latitude"].median()), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, fontsize=8, color=TEXTO, zorder=4,
                    bbox=dict(boxstyle="round,pad=0.15", fc=SUPERFICIE, ec="none", alpha=0.75))
    ax.set_aspect(1 / math.cos(math.radians(22.9)))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("UBS ativas na Região Metropolitana de Campinas (coordenadas do CNES)")
    salvar(fig, "07_mapa_ubs.png")


# ---------------------------------------------------------------- estatisticas

def correlacoes(d):
    linhas = []
    variaveis = {"renda_2010": "renda domiciliar per capita 2010", "gini_2010": "índice de Gini 2010",
                 "pib_pc_2023": "PIB per capita 2023", "ubs_por_100mil_hab": "UBS por 100 mil habitantes",
                 "cobertura_sisvan_pct": "cobertura do SISVAN"}
    amostras = {"todos os municípios": d, "cobertura do SISVAN de 5% ou mais": d[d["cobertura_sisvan_pct"] >= COBERTURA_MINIMA]}
    for nome_amostra, base in amostras.items():
        for col, rotulo in variaveis.items():
            rho, p = spearmanr(base["obesidade_pct"], base[col])
            linhas.append({"variavel": col, "descricao": rotulo, "amostra": nome_amostra, "n": len(base), "rho": rho, "p": p})
    return pd.DataFrame(linhas)


def relacoes_auxiliares(d):
    """Correlacoes entre as proprias variaveis explicativas, para saber se elas se confundem."""
    pares = [("ubs_por_100mil_hab", "populacao_total"), ("ubs_por_100mil_hab", "cobertura_sisvan_pct"),
             ("cobertura_sisvan_pct", "populacao_total"), ("obesidade_pct", "populacao_total")]
    linhas = []
    for a, b in pares:
        rho, p = spearmanr(d[a], d[b])
        linhas.append({"variavel_a": a, "variavel_b": b, "n": len(d), "rho": round(rho, 3), "p": round(p, 4)})
    return pd.DataFrame(linhas)


def main():
    RESULTADOS.mkdir(exist_ok=True)
    con = sqlite3.connect(BANCO)
    for arquivo in sorted(CONSULTAS.glob("q*.sql")):
        consulta(con, arquivo.name).to_csv(RESULTADOS / (arquivo.stem + ".csv"), index=False)
    d = pd.read_sql_query("SELECT * FROM v_indicadores", con)
    cor = correlacoes(d)
    cor.round({"rho": 3, "p": 4}).to_csv(RESULTADOS / "correlacoes_spearman.csv", index=False)

    aux = relacoes_auxiliares(d)
    aux.to_csv(RESULTADOS / "relacoes_entre_variaveis.csv", index=False)
    rho_cob = cor[(cor["variavel"] == "cobertura_sisvan_pct") & (cor["amostra"] == "todos os municípios")].iloc[0]
    grafico_obesidade(d)
    grafico_cobertura(d)
    grafico_cobertura_vs_obesidade(d, rho_cob["rho"], rho_cob["p"])
    grafico_socioeconomia(d, cor)
    grafico_ubs(d)
    grafico_quadrante(d)
    grafico_mapa(con)
    con.close()
    print(cor.round({"rho": 2, "p": 3}).to_string(index=False))
    print(aux.to_string(index=False))
    print("Gráficos salvos em", GRAFICOS.relative_to(RAIZ))


if __name__ == "__main__":
    main()
