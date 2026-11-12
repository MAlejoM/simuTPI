"""Generate report figures from the native 24x7 run and historical 2025 demand."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "domitec_interactivo" / "resultados_operativos_v2" / "comparacion_20261111_194531_208"
DEMAND = ROOT / "demanda" / "demanda - Sheet1.csv"
OUT = ROOT / "figuras"
COLORS = {0: "#2878B5", 1: "#E6862A", 2: "#2A9D55"}
SCENARIOS = {0: "Base 24×7", 1: "Sin pánico 24×7", 2: "Rendimiento +27,5%"}
MONTHS = ["Ene.", "Feb.", "Mar.", "Abr.", "May.", "Jun.", "Jul.", "Ago.", "Sept.", "Oct.", "Nov.", "Dic."]
FAMILIES = {
    "LAVANDINA COMUN": "Lavandina", "LAVANDINA CONCENTRADA": "Lavandina",
    "LIQUIDO DESINFECTANTE": "Desinfectante", "LAVAVAJILLA": "Lavavajilla",
    "LIQUIDO LAVAR ROPA": "Lavarropa", "SUAVIZANTE": "Suavizante",
    "DETERGENTE CONCENTRADO": "Detergente concentrado",
}


def read_native_series():
    rows = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    seeds = defaultdict(set)
    with (RUN / "series_semanales.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            s, e, w = int(r["seed"]), int(r["escenario"]), int(float(r["semana"]))
            seeds[e].add(s)
            for col in ("demanda", "ordenes", "produccion", "backlog", "wip"):
                rows[e][col][w].append(float(r[col]))
    if any(len(seeds[e]) != 100 for e in range(3)):
        raise ValueError("La serie debe incluir 100 réplicas por escenario")
    means = {e: {k: np.array([np.mean(rows[e][k][w]) for w in range(100)])
                 for k in ("demanda", "ordenes", "produccion", "backlog", "wip")}
             for e in range(3)}
    if any(len(means[e]["backlog"]) != 100 for e in range(3)):
        raise ValueError("Se esperan exactamente 100 semanas por escenario")
    return means


def save_timeseries():
    m = read_native_series()
    weeks = np.arange(100)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.4,
                         "axes.titlesize": 10.2, "axes.labelsize": 9.4,
                         "legend.fontsize": 8.5, "pdf.fonttype": 42,
                         "ps.fonttype": 42, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 6.8))
    # Reserve a separate band for the two-line legend and figure title.
    fig.subplots_adjust(left=0.12,right=0.985,bottom=0.075,top=0.80,wspace=0.36,hspace=0.43)
    panels = [("ordenes", "Órdenes semanales", "Cajas/semana", True),
              ("produccion", "Producción semanal", "Cajas/semana", True),
              ("backlog", "Pedidos pendientes", "Cajas", False),
              ("wip", "Trabajo en proceso (WIP)", "Cajas", False)]
    for ax, (key, title, ylabel, with_demand) in zip(axs.flat, panels):
        ax.axvspan(0, 15, color="#E9EEF2", zorder=0, label="Warm-up (0–15 sem.)")
        if with_demand:
            ax.plot(weeks, m[0]["demanda"], color="#222222", linewidth=1.8,
                    label="Demanda común", zorder=4)
        for e in range(3):
            ax.plot(weeks, m[e][key], color=COLORS[e], linewidth=1.6,
                    label=SCENARIOS[e], zorder=3)
        ax.set_title(title, loc="left", fontweight="bold", pad=7)
        ax.set_xlabel("Semana")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 99)
        ax.set_xticks(np.arange(0, 100, 10))
        ax.grid(axis="y", color="#D9DEE3", linewidth=0.6)
        ax.set_axisbelow(True)
    handles, labels = axs[0, 0].get_legend_handles_labels()
    legend=fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.53, 0.945),
               ncol=3, frameon=False, handlelength=1.8, columnspacing=1.6)
    fig.suptitle("Evolución semanal promedio de 100 réplicas por escenario",
                 y=0.985, fontsize=12.0, fontweight="bold")
    for ax, letter in zip(axs.flat, "abcd"):
        ax.set_title(f"({letter}) "+ax.get_title(loc="left"),loc="left",fontweight="bold",fontsize=10.2,pad=7)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"series_modelo_24x7.{ext}", dpi=200,
                    bbox_inches="tight", pad_inches=0.16,
                    metadata={"Title": "Series semanales del modelo 24x7"})
    # Geometry check: all axes and labels must remain inside the rendered canvas.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.get_window_extent(renderer)
    if legend.get_window_extent(renderer).y0 <= max(ax.get_tightbbox(renderer).y1 for ax in axs[0]):
        raise RuntimeError("La leyenda invade los paneles de la figura")
    for ax in axs.flat:
        box = ax.get_tightbbox(renderer)
        if box.x0 < bounds.x0 - 1 or box.y0 < bounds.y0 - 1 or box.x1 > bounds.x1 + 1 or box.y1 > bounds.y1 + 1:
            raise RuntimeError("Recorte detectado en la figura de series")
    plt.close(fig)


def parse_num(v):
    return float((v or "0").strip().replace(".", "").replace(",", "."))


def save_historical():
    months = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0, 0.0]))
    with DEMAND.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("Año") != "2025" or row.get("Mes") not in MONTHS or row.get("RubroDes") not in FAMILIES:
                continue
            family = FAMILIES[row["RubroDes"]]
            month = MONTHS.index(row["Mes"])
            values = months[family][month]
            values[0] += parse_num(row.get("Pedidos"))
            values[1] += parse_num(row.get("Despachadas"))
            values[2] += parse_num(row.get("Cancelado"))
    names = ["Lavandina", "Desinfectante", "Lavavajilla", "Lavarropa", "Suavizante", "Detergente concentrado"]
    x = np.arange(12)
    fig, ax = plt.subplots(figsize=(7.0, 3.6), constrained_layout=True)
    totals = sum(np.array([months[name][j] for j in range(12)]) for name in names) / 1000.0
    for col,label,color,style in [(0,"Pedidas","#222222","-"),(1,"Despachadas","#2878B5","--"),(2,"Canceladas","#E6862A",":")]:
        ax.plot(x,totals[:,col],marker="o",ms=3.3,lw=1.7,color=color,ls=style,label=label)
    ax.set_title("Demanda histórica 2025: seis familias agregadas", loc="left", fontweight="bold", pad=10)
    ax.set_xlabel("Mes")
    ax.set_ylabel("Miles de cajas")
    ax.set_xticks(x, [m.rstrip(".") for m in MONTHS])
    ax.grid(axis="y", color="#D9DEE3", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.18),
              columnspacing=1.35, handlelength=1.5, fontsize=9.0)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"demanda_historica_2025.{ext}", dpi=200,
                    bbox_inches="tight", pad_inches=0.16,
                    metadata={"Title": "Demanda histórica 2025 por familia"})
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.get_window_extent(renderer)
    if ax.get_tightbbox(renderer).x0 < bounds.x0 - 1 or ax.get_tightbbox(renderer).y0 < bounds.y0 - 1 or ax.get_tightbbox(renderer).x1 > bounds.x1 + 1 or ax.get_tightbbox(renderer).y1 > bounds.y1 + 1:
        raise RuntimeError("Recorte detectado en la figura de demanda histórica")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    save_timeseries()
    save_historical()
    print("Generadas 2 figuras en PNG (200 dpi) y PDF vectorial:", OUT)


if __name__ == "__main__":
    main()
