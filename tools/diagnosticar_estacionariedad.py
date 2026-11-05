#!/usr/bin/env python3
"""Diagnóstico descriptivo de series semanales de una salida 100x3 real.

Promedia las réplicas por semana y escenario, aplica una media móvil centrada
de cinco semanas para visualizar la tendencia, y calcula cambios de medias y
pendientes OLS. No ejecuta ni declara una prueba formal de estacionariedad.
"""

from __future__ import annotations

import argparse
import csv
import html
import math
import sys
from collections import defaultdict
from pathlib import Path

VARIABLES = ("demanda", "produccion", "stock", "backlog", "wip")
COLORES = {0: "#1769aa", 1: "#ef6c00", 2: "#388e3c"}
ETIQUETA = "NO ESTACIONARIEDAD DEMOSTRADA — DIAGNÓSTICO DESCRIPTIVO"


def encontrar_entrada(dado: Path | None) -> Path:
    if dado is not None:
        return dado
    raiz = Path.cwd() / "resultados_domitec"
    opciones = sorted(raiz.glob("comparacion_*/series_semanales.csv"), key=lambda p: p.stat().st_mtime)
    if not opciones:
        raise FileNotFoundError(
            "No existe una serie real en resultados_domitec/comparacion_*/series_semanales.csv; "
            "no se generaron ni exportaron datos sintéticos."
        )
    return opciones[-1]


def cargar(path: Path) -> tuple[dict, float, dict[int, set[int]]]:
    if not path.is_file():
        raise FileNotFoundError(f"No se encontró la serie semanal: {path}")
    sums = defaultdict(lambda: [0.0, 0])
    seen = set()
    seeds_por_esc = {s: set() for s in range(3)}
    semanas_por_run = defaultdict(set)
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        requeridas = {"seed", "escenario", "semana", *VARIABLES}
        if reader.fieldnames is None or not requeridas.issubset(set(reader.fieldnames)):
            raise ValueError(f"Cabecera inválida. Se requieren columnas {sorted(requeridas)}")
        for n, row in enumerate(reader, 2):
            try:
                seed = int(row["seed"])
                scenario = int(row["escenario"])
                week = float(row["semana"])
                vals = {v: float(row[v]) for v in VARIABLES}
            except (TypeError, ValueError) as e:
                raise ValueError(f"Fila {n}: semilla/escenario/semana/métrica no numérica") from e
            if not (1 <= seed <= 100 and 0 <= scenario <= 2 and math.isfinite(week)):
                raise ValueError(f"Fila {n}: ID de semilla, escenario o semana fuera de rango")
            if any(not math.isfinite(x) for x in vals.values()):
                raise ValueError(f"Fila {n}: hay valores no finitos")
            key = (seed, scenario, week)
            if key in seen:
                raise ValueError(f"Fila {n}: semana duplicada para seed={seed}, escenario={scenario}, semana={week}")
            seen.add(key)
            seeds_por_esc[scenario].add(seed)
            semanas_por_run[(seed, scenario)].add(week)
            for variable, value in vals.items():
                slot = sums[(scenario, week, variable)]
                slot[0] += value
                slot[1] += 1
    if not seen:
        raise ValueError("El CSV semanal no contiene filas")
    for s in range(3):
        if len(seeds_por_esc[s]) != 100:
            raise ValueError(f"Escenario {s}: se hallaron {len(seeds_por_esc[s])} semillas, se esperaban 100")
    for scenario in range(3):
        for seed in range(1, 101):
            if len(semanas_por_run[(seed, scenario)]) != 100:
                raise ValueError(f"Seed {seed}, escenario {scenario}: no hay 100 observaciones semanales únicas")
    weekly = {}
    for key, (total, n) in sums.items():
        weekly[key] = total / n
    return weekly, leer_warmup(path.parent / "metadata.txt"), seeds_por_esc


def leer_warmup(metadata: Path) -> float:
    if not metadata.is_file():
        raise FileNotFoundError(f"Falta metadata.txt junto a las series: {metadata}")
    for line in metadata.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("warmup_weeks="):
            try:
                value = float(line.split("=", 1)[1])
            except ValueError as e:
                raise ValueError("warmup_weeks inválido en metadata") from e
            if not math.isfinite(value) or value < 0:
                raise ValueError("warmup_weeks debe ser finito y no negativo")
            return value
    raise ValueError("metadata.txt no declara warmup_weeks")


def suavizado_welch5(values: list[float]) -> list[float]:
    """Ventana Welch de cinco puntos, centrada y renormalizada en los bordes."""
    out = []
    for i in range(len(values)):
        left, right = max(0, i - 2), min(len(values), i + 3)
        numerador = denominador = 0.0
        for j in range(left, right):
            offset = j - i
            weight = 1.0 - (offset / 3.0) ** 2
            numerador += values[j] * weight
            denominador += weight
        out.append(numerador / denominador)
    return out


def media(values: list[float]) -> float:
    return sum(values) / len(values)


def pendiente_ols(xs: list[float], ys: list[float]) -> float:
    xm, ym = media(xs), media(ys)
    den = sum((x - xm) ** 2 for x in xs)
    return 0.0 if den == 0.0 else sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / den


def calcular(weekly: dict, warmup: float) -> tuple[list[dict], dict]:
    all_series = {}
    summaries = []
    for scenario in range(3):
        for variable in VARIABLES:
            pairs = sorted(
                (week, val) for (s, week, v), val in weekly.items()
                if s == scenario and v == variable and week >= warmup
            )
            if len(pairs) < 4:
                raise ValueError(f"Escenario {scenario}, {variable}: se necesitan al menos 4 semanas post-warm-up")
            weeks = [x for x, _ in pairs]
            raw = [y for _, y in pairs]
            smooth = suavizado_welch5(raw)
            all_series[(scenario, variable)] = (weeks, raw, smooth)
            split = len(raw) // 2
            first, second = raw[:split], raw[split:]
            summaries.append({
                "tipo": "resumen", "escenario": scenario, "variable": variable,
                "warmup_semanas": warmup, "n_semanas": len(raw),
                "media_primera_mitad": media(first), "media_segunda_mitad": media(second),
                "diferencia_segunda_menos_primera": media(second) - media(first),
                "pendiente_ols_por_semana": pendiente_ols(weeks, raw),
                "estado": "NO ESTACIONARIEDAD DEMOSTRADA — DIAGNÓSTICO DESCRIPTIVO",
            })
            summaries.extend({
                "tipo": "serie", "escenario": scenario, "variable": variable,
                "warmup_semanas": warmup, "semana": w,
                "media_ensemble": y, "suavizado_welch_5_puntos": sm,
                "estado": "NO ESTACIONARIEDAD DEMOSTRADA — DIAGNÓSTICO DESCRIPTIVO",
            } for w, y, sm in zip(weeks, raw, smooth))
    return summaries, all_series


def escribir_csv(path: Path, records: list[dict]) -> None:
    fields = ["tipo", "escenario", "variable", "warmup_semanas", "n_semanas", "media_primera_mitad",
              "media_segunda_mitad", "diferencia_segunda_menos_primera", "pendiente_ols_por_semana",
              "semana", "media_ensemble", "suavizado_welch_5_puntos", "estado"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def escribir_svg(path: Path, series: dict) -> None:
    width, panel_h, margin_l, margin_r, margin_t = 1120, 250, 90, 35, 105
    height = margin_t + panel_h * len(VARIABLES) + 45
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{width/2}" y="32" text-anchor="middle" font-family="sans-serif" font-size="21" font-weight="bold">{html.escape(ETIQUETA)}</text>',
             '<text x="50" y="63" font-family="sans-serif" font-size="13">Promedio entre semillas; suavizado Welch centrado de 5 puntos (visualización, no prueba formal)</text>']
    for var_i, variable in enumerate(VARIABLES):
        y0 = margin_t + var_i * panel_h
        x0, plot_w, plot_h = margin_l, width - margin_l - margin_r, panel_h - 48
        vals = [y for scenario in range(3) for y in series[(scenario, variable)][2]]
        lo, hi = min(vals), max(vals)
        if hi == lo:
            pad = max(1.0, abs(lo) * 0.05)
            lo, hi = lo - pad, hi + pad
        else:
            pad = (hi - lo) * 0.08
            lo, hi = lo - pad, hi + pad
        parts.append(f'<text x="{x0}" y="{y0+18}" font-family="sans-serif" font-size="16" font-weight="bold">{html.escape(variable)}</text>')
        parts.append(f'<line x1="{x0}" y1="{y0+plot_h}" x2="{x0+plot_w}" y2="{y0+plot_h}" stroke="#555"/>')
        parts.append(f'<line x1="{x0}" y1="{y0+30}" x2="{x0}" y2="{y0+plot_h}" stroke="#555"/>')
        parts.append(f'<text x="{x0+plot_w/2}" y="{y0+plot_h+31}" text-anchor="middle" font-family="sans-serif" font-size="12">Semana</text>')
        for scenario in range(3):
            weeks, _raw, smooth = series[(scenario, variable)]
            min_w, max_w = min(weeks), max(weeks)
            span_w = max(max_w - min_w, 1.0)
            points = []
            for w, value in zip(weeks, smooth):
                x = x0 + ((w - min_w) / span_w) * plot_w
                y = y0 + 30 + (1 - (value - lo) / (hi - lo)) * (plot_h - 30)
                points.append(f"{x:.1f},{y:.1f}")
            parts.append(f'<polyline fill="none" stroke="{COLORES[scenario]}" stroke-width="2" points="{" ".join(points)}"/>')
            ly = y0 + 18
            lx = x0 + 150 + scenario * 135
            parts.append(f'<line x1="{lx}" y1="{ly-5}" x2="{lx+22}" y2="{ly-5}" stroke="{COLORES[scenario]}" stroke-width="3"/>')
            parts.append(f'<text x="{lx+27}" y="{ly}" font-family="sans-serif" font-size="12">Escenario {scenario}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="ruta a series_semanales.csv real")
    parser.add_argument("--out-dir", type=Path, help="directorio de salida (por defecto, junto al CSV)")
    args = parser.parse_args(argv)
    try:
        input_path = encontrar_entrada(args.input)
        weekly, warmup, _seeds = cargar(input_path)
        records, series = calcular(weekly, warmup)
        output_dir = args.out_dir or input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = output_dir / "diagnostico_estacionariedad.csv"
        svg_path = output_dir / "diagnostico_estacionariedad.svg"
        escribir_csv(csv_path, records)
        escribir_svg(svg_path, series)
    except (OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print(f"Fuente: {input_path}")
    print(f"CSV diagnóstico: {csv_path}")
    print(f"SVG diagnóstico: {svg_path}")
    print(ETIQUETA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
