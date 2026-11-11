#!/usr/bin/env python3
"""Reproducible read-only analysis of operational demand and production CSVs."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMAND = ROOT / "demanda" / "demanda - Sheet1.csv"
PROD = ROOT / "produccion" / "prod.csv"
PROD1 = ROOT / "produccion" / "prod1.csv"
PROD3 = ROOT / "produccion" / "prod3.csv"
JSON_OUT = ROOT / "docs" / "diagnostico_datos_operativos.json"
MD_OUT = ROOT / "docs" / "diagnostico_datos_operativos.md"

FAMILY_MAP = {
    "LAVANDINA COMUN": "Lavandina",
    "LAVANDINA CONCENTRADA": "Lavandina",
    "LAVAVAJILLA": "Lavavajilla",
    "LIQUIDO DESINFECTANTE": "Desinfectante",
    "LIQUIDO LAVAR ROPA": "Lavarropa",
    "SUAVIZANTE": "Suavizante",
    "DETERGENTE CONCENTRADO": "Detergente concentrado",
}
EXCLUDED_DEMAND = {"PROMOPACK", "LIQUIDO LIMPIADOR", "LIQUIDO BACTERICIDA"}
MONTHS = ["Ene.", "Feb.", "Mar.", "Abr.", "May.", "Jun.", "Jul.", "Ago.", "Sept.", "Oct.", "Nov.", "Dic."]


def read_csv(path: Path, delimiter: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def number(value: str | None) -> float:
    """Parse Spanish-formatted numbers (dot thousands, comma decimal)."""
    s = (value or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def clean(v: float) -> int | float:
    return int(v) if float(v).is_integer() else round(v, 4)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sum_fields(rows: list[dict[str, str]], fields: list[str]) -> dict[str, int | float]:
    return {f: clean(sum(number(r.get(f)) for r in rows)) for f in fields}


def demand_analysis() -> dict:
    rows = read_csv(DEMAND, ",")
    total_rows = [r for r in rows if (r.get("Año") or "").strip().casefold() == "total"]
    actual = [r for r in rows if (r.get("Año") or "").strip().isdigit()]
    fields = ["Pedidos", "Despachadas", "Cancelado", "Pendientes"]
    equation_errors = []
    for i, r in enumerate(actual, start=2):
        if number(r["Pedidos"]) != number(r["Despachadas"]) + number(r["Cancelado"]) + number(r["Pendientes"]):
            equation_errors.append(i)
    by_year, by_month, by_rubro, by_family = {}, {}, {}, {}
    def grouped(keyfn):
        groups = defaultdict(list)
        for row in actual:
            groups[keyfn(row)].append(row)
        return {" / ".join(map(str, k if isinstance(k, tuple) else (k,))): sum_fields(v, fields)
                for k, v in sorted(groups.items(), key=lambda kv: tuple(map(str, kv[0] if isinstance(kv[0], tuple) else (kv[0],))))}
    by_year = grouped(lambda r: r["Año"])
    by_month = grouped(lambda r: (r["Año"], r["Mes"]))
    by_rubro = grouped(lambda r: (r["Año"], r["RubroDes"]))
    family_rows = [r for r in actual if r["RubroDes"] in FAMILY_MAP]
    family_groups = defaultdict(list)
    for row in family_rows:
        family_groups[(row["Año"], FAMILY_MAP[row["RubroDes"]])].append(row)
    by_family = {" / ".join(k): sum_fields(v, fields) for k, v in sorted(family_groups.items())}
    family_month_groups = defaultdict(list)
    for row in family_rows:
        family_month_groups[(row["Año"], row["Mes"], FAMILY_MAP[row["RubroDes"]])].append(row)
    by_family_month = {" / ".join(k): sum_fields(v, fields) for k, v in sorted(family_month_groups.items())}
    key_fields = ["Año", "VentasXnegocio", "Mes", "Cliente", "RubroDes", "PresentacionDes"]
    keys = [tuple(r.get(k, "") for k in key_fields) for r in actual]
    duplicate_count = len(keys) - len(set(keys))
    return {
        "source": DEMAND.relative_to(ROOT).as_posix(), "source_sha256": sha256(DEMAND),
        "row_count_including_total": len(rows), "actual_row_count": len(actual),
        "summary_total_row_count_excluded": len(total_rows), "summary_total_row_values": [sum_fields([r], fields) for r in total_rows],
        "units": "Not specified in source. Packaging descriptions suggest case/pack context, but no unit is asserted.",
        "periods": {"years": sorted({r["Año"] for r in actual}), "months_seen_by_year": {
            y: [m for m in MONTHS if any(r["Año"] == y and r["Mes"] == m for r in actual)] for y in sorted({r["Año"] for r in actual})}},
        "equation": "Pedidos = Despachadas + Cancelado + Pendientes",
        "equation_mismatch_count": len(equation_errors), "equation_mismatch_csv_line_numbers": equation_errors,
        "duplicate_count_on_year_business_month_client_rubro_presentation": duplicate_count,
        "annual_totals": by_year, "monthly_totals_year_month": by_month,
        "rubro_totals_year_rubro": by_rubro, "family_totals_year_family": by_family,
        "family_totals_year_month_family": by_family_month,
        "family_mapping": FAMILY_MAP,
        "excluded_from_six_family_channel_rollup": sorted(EXCLUDED_DEMAND),
        "excluded_rubro_totals_year_rubro": {" / ".join(k): sum_fields(v, fields) for k, v in sorted(
            ((y, rubro), [r for r in actual if r["Año"] == y and r["RubroDes"] == rubro])
            for y in sorted({r["Año"] for r in actual}) for rubro in sorted(EXCLUDED_DEMAND)
            if any(r["Año"] == y and r["RubroDes"] == rubro for r in actual))},
        "comparison_note": "Demand has explicit years; production files have no year. Annual demand and production totals therefore are not asserted as like-for-like or causally comparable.",
    }


def production_analysis() -> dict:
    rows = read_csv(PROD, ";")
    rows = [r for r in rows if (r.get("RtoMes") or "").strip()]
    complete = [r for r in rows if r["RtoMes"] in MONTHS[:8]]
    by_rubro = defaultdict(list)
    by_family = defaultdict(list)
    for r in complete:
        by_rubro[r["RubroDes"]].append(r)
        if r["RubroDes"] in FAMILY_MAP:
            by_family[FAMILY_MAP[r["RubroDes"]]].append(r)
    rate_table = {}
    for family, rs in sorted(by_family.items()):
        cajas = sum(number(r["Cajas"]) for r in rs)
        tiempo = sum(number(r["Tiempo"]) for r in rs)
        line_rate = cajas / (tiempo / 60) if tiempo else None
        # Prod/Hs/Ho is interpreted only as the source label; multiplying by
        # Operarios yields an observed/expected line-rate proxy, weighted by time.
        hours = [number(r["Tiempo"]) / 60 for r in rs]
        predicted_line_rate = (sum(number(r["Prod/Hs/Ho"]) * number(r["Operarios"]) * h for r, h in zip(rs, hours)) / sum(hours)) if sum(hours) else None
        rate_table[family] = {
            "rubro_members": sorted({r["RubroDes"] for r in rs}),
            "jan_aug_rows": len(rs), "cajas_jan_aug": clean(cajas),
            "tiempo_source_units_jan_aug": clean(tiempo),
            "observed_cajas_per_hour_if_tiempo_is_minutes": round(line_rate, 3) if line_rate is not None else None,
            "mean_prod_hs_ho_per_row_unweighted": round(sum(number(r["Prod/Hs/Ho"]) for r in rs) / len(rs), 3),
            "mean_operarios_per_row_unweighted": round(sum(number(r["Operarios"]) for r in rs) / len(rs), 3),
            "time_weighted_prod_hs_ho_times_operarios_line_rate_proxy": round(predicted_line_rate, 3) if predicted_line_rate is not None else None,
            "ratio_observed_to_prod_hs_ho_times_operarios": round(line_rate / predicted_line_rate, 4) if line_rate is not None and predicted_line_rate else None,
        }
    monthly = {}
    for m in MONTHS:
        rs = [r for r in rows if r["RtoMes"] == m]
        if rs:
            monthly[m] = {"row_count": len(rs), "totals": sum_fields(rs, ["Cajas", "Tiempo"])}
    rubro = {k: {"jan_aug_row_count": len(v), **sum_fields(v, ["Cajas", "Tiempo"]),
                 "observed_cajas_per_hour_if_tiempo_is_minutes": round(sum(number(r["Cajas"]) for r in v)/(sum(number(r["Tiempo"]) for r in v)/60), 3) if sum(number(r["Tiempo"]) for r in v) else None}
              for k, v in sorted(by_rubro.items())}
    all_prod1 = read_csv(PROD1, ";")
    p1rows = [r for r in all_prod1 if (r.get("RtoMes") or "").strip()]
    keys = [(r.get("RtoMes", ""), r.get("RubroDes", ""), r.get("Pres", "")) for r in p1rows]
    capacity_rows = read_csv(PROD3, ";")
    capacity = {}
    for r in capacity_rows:
        label = (r.get("Lineas") or "").strip()
        if label and label.casefold() not in {"lineas", "recursos de produccion"}:
            capacity[label] = {"production_per_hour": number(r.get("Produccion/ hr")), "availability_hours_per_month": number(r.get("disponibilidad hr/mes")) if r.get("disponibilidad hr/mes") else None}
    line_caps = {
        "Lavandina": ("lavandina", ["LAVANDINA COMUN", "LAVANDINA CONCENTRADA"]),
        "Lavavajilla": ("lavavajilla", ["LAVAVAJILLA"]),
        "Desinfectante": ("liq desinfectante", ["LIQUIDO DESINFECTANTE"]),
        "Lavarropa": ("liq lavar ropa", ["LIQUIDO LAVAR ROPA"]),
        "Suavizante": ("sauvizante", ["SUAVIZANTE"]),
        "Detergente concentrado": ("detergente conc", ["DETERGENTE CONCENTRADO"]),
    }
    for family, (line, members) in line_caps.items():
        rate_table.setdefault(family, {"rubro_members": members})
        cap = capacity.get(line, {})
        rate_table[family]["prod3_line_label"] = line
        rate_table[family]["prod3_nominal_rate_cajas_per_hour_label"] = cap.get("production_per_hour")
        rate_table[family]["prod3_availability_hours_per_month"] = cap.get("availability_hours_per_month")
        rate = cap.get("production_per_hour")
        hrs = cap.get("availability_hours_per_month")
        rate_table[family]["prod3_nominal_monthly_capacity"] = clean(rate * hrs) if rate is not None and hrs is not None else None
    lav = rate_table.get("Lavandina", {})
    lav["mapping_note"] = "Both lavandina rubros map to one prod3 line/rate; do not double the line capacity. January-August pooled observed rate is computed over combined boxes and combined Tiempo."
    prod_totals = sum_fields(complete, ["Cajas", "Tiempo"])
    return {
        "source": PROD.relative_to(ROOT).as_posix(), "source_sha256": sha256(PROD),
        "year": None, "year_note": "No year field is present; do not equate these months with demand 2025 without external confirmation.",
        "main_file": "prod.csv", "prod1_role": "Separate variant/subset, not additive to prod.csv.",
        "prod1_source_sha256": sha256(PROD1), "prod1_nonblank_data_rows": len(p1rows),
        "prod1_duplicate_month_rubro_presentation_keys": len(keys) - len(set(keys)),
        "prod1_comparison_totals_not_for_addition": sum_fields(p1rows, ["Cajas", "Tiempo"]),
        "prod3_source": PROD3.relative_to(ROOT).as_posix(), "prod3_source_sha256": sha256(PROD3),
        "period_months_present": list(monthly), "jan_aug_complete_months_used_for_rates": MONTHS[:8],
        "september_partial_note": "September has substantially fewer rows and lower Cajas than prior months; treated as partial and excluded from rate calibration.",
        "prod3_capacity_by_line": capacity, "monthly_totals": monthly,
        "jan_aug_totals": prod_totals, "jan_aug_rubro_totals": rubro,
        "family_rate_calibration": rate_table,
        "time_unit_caveat": "The source does not define Tiempo units. Observed Cajas/(Tiempo/60) assumes Tiempo is minutes; validate before using as calibrated rate.",
        "prod_hs_ho_interpretation": "Column labels suggest Prod/Hs/Ho is per-person hourly productivity; the diagnostic contrasts its time-weighted product with Operarios against the observed line rate, without claiming the source defines the formula.",
    }


def markdown(report: dict) -> str:
    d, p = report["demand"], report["production"]
    lines = ["# Diagnóstico de datos operativos", "",
             "Generado por `tools/analizar_datos_operativos.py`. Los CSV fuente se leen sin modificarlos.", "",
             "## Alcance y calidad", "",
             f"- Demanda: {d['actual_row_count']:,} registros con año; se excluyeron {d['summary_total_row_count_excluded']} fila(s) de resumen `Total`.",
             f"- Ecuación Pedidos = Despachadas + Cancelado + Pendientes: {d['equation_mismatch_count']} discrepancias.",
             f"- Duplicados por año, negocio, mes, cliente, rubro y presentación: {d['duplicate_count_on_year_business_month_client_rubro_presentation']}.",
             "- Las unidades de demanda no están declaradas. Producción no tiene año; sus totales no son directamente comparables con los años de demanda.",
             "- `prod.csv` es la fuente principal; `prod1.csv` es variante/subconjunto y no se suma. Septiembre de `prod.csv` se excluye de tasas por aparente parcialidad.",
             "- La familia Lavandina combina común y concentrada, pero se asigna a una sola línea/rate `lavandina` de `prod3.csv`.",
             "- Se excluyen de las seis familias comparables: PROMOPACK, LÍQUIDO LIMPIADOR y LÍQUIDO BACTERICIDA.", "",
             "## Demanda anual", "", "| Año | Pedidos | Despachadas | Cancelado | Pendientes |", "|---:|---:|---:|---:|---:|"]
    for year, vals in d["annual_totals"].items():
        lines.append(f"| {year} | {vals['Pedidos']:,} | {vals['Despachadas']:,} | {vals['Cancelado']:,} | {vals['Pendientes']:,} |")
    lines += ["", "## Tasa observada para calibración (prod.csv, ene–ago)", "",
              "`Tiempo` se interpreta provisionalmente como minutos. Tasa observada = suma Cajas / (suma Tiempo / 60). La producción no tiene año.", "",
              "| Familia | Rubros incluidos | Cajas ene–ago | Cajas/h observado* | Prod/Hs/Ho prom. | Operarios prom. | (Prod/Hs/Ho × Operarios), ponderado por tiempo | prod3 nominal/h | prod3 h/mes | prod3 capacidad/mes |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for family, a in sorted(p["family_rate_calibration"].items()):
        members = ", ".join(a.get("rubro_members", []))
        fmt = lambda x: "—" if x is None else f"{x:,.2f}" if isinstance(x, float) else f"{x:,}"
        lines.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            family, members, fmt(a.get("cajas_jan_aug")), fmt(a.get("observed_cajas_per_hour_if_tiempo_is_minutes")),
            fmt(a.get("mean_prod_hs_ho_per_row_unweighted")), fmt(a.get("mean_operarios_per_row_unweighted")),
            fmt(a.get("time_weighted_prod_hs_ho_times_operarios_line_rate_proxy")),
            fmt(a.get("prod3_nominal_rate_cajas_per_hour_label")), fmt(a.get("prod3_availability_hours_per_month")),
            fmt(a.get("prod3_nominal_monthly_capacity"))))
    lav = p["family_rate_calibration"].get("Lavandina", {})
    lines += ["", "* Lavandina es una única línea: tasa pooled común + concentrada = **{} cajas/h**; producción acumulada ene–ago = **{} cajas**, suma de Tiempo = **{} min** ({} h/mes promedio si Tiempo está en minutos). Capacidad nominal prod3 = **{} cajas/mes** (235 × 330), una línea; no se duplica por tener dos rubros.".format(
        lav.get("observed_cajas_per_hour_if_tiempo_is_minutes", "—"), lav.get("cajas_jan_aug", "—"),
        lav.get("tiempo_source_units_jan_aug", "—"), round(number(str(lav.get("tiempo_source_units_jan_aug", 0))) / 60 / 8, 1),
        lav.get("prod3_nominal_monthly_capacity", "—")), "",
        "`Prod/Hs/Ho` parece una tasa por operario: en el primer renglón de prod.csv, 3,499 / (1,790/60) = 117.3 cajas/h de línea; dividido por 4 operarios = 29.3, coincidente con Prod/Hs/Ho=29. En los agregados se muestra la comparación como contraste de etiqueta, no como definición confirmada.", "",
        "## Demanda por mes", "",
        "Los totales completos por año/mes, por rubro y por canal de seis familias están en el JSON adjunto; se mantienen allí para evitar una tabla extensa en este resumen.", "",
        "## Fuentes y huellas SHA-256", "",
        "| Fuente | SHA-256 |", "|---|---|"]
    for path, digest in [(d["source"], d["source_sha256"]), (p["source"], p["source_sha256"]), ("produccion/prod1.csv", p["prod1_source_sha256"]), (p["prod3_source"], p["prod3_source_sha256"])]:
        lines.append(f"| `{path}` | `{digest}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    report = {"title": "Diagnóstico de datos operativos", "demand": demand_analysis(), "production": production_analysis()}
    JSON_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MD_OUT.write_text(markdown(report), encoding="utf-8")
    print(f"Wrote {JSON_OUT.relative_to(ROOT)}")
    print(f"Wrote {MD_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
