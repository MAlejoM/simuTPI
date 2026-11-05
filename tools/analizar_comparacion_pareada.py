#!/usr/bin/env python3
"""Audita y compara resultados AnyLogic por identificador de réplica.

Solo usa la biblioteca estándar. Por defecto lee ../csv/esc{0,1,2}.txt,
verifica el diseño de semillas y horizonte en main_con_3d/Domitec_Main_3D.alp,
calcula IC t pareados y escribe tools/auditoria_estadistica.md.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

N_ESPERADO = 100
T_CRIT_99 = 1.9842169515
PARES = ((0, 1), (0, 2), (1, 2))
KPI = ("Fill Rate (%)", "Backlog (cajas)", "Razón BW", "Stock depósito (cajas)")
LINEA = re.compile(
    r"\[REPLICA\s*#(?P<rep>\d+)\]\s*Fill Rate:\s*"
    r"(?P<fill>[+-]?(?:\d+(?:\.\d*)?|\.\d+))%\s*\|\s*"
    r"Backlog:\s*(?P<backlog>[\d.,]+)\s*cajas\s*\|\s*"
    r"Razon\s+BW:\s*(?P<bw>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\|\s*"
    r"Stock\s+Deposito:\s*(?P<stock>[\d.,]+)\s*cajas",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Resultado:
    replica: int
    valores: tuple[float, float, float, float]
    linea: int


def numero_entero_agrupado(texto: str) -> int:
    """Admite agrupación de miles con coma o punto, sin inferir decimales."""
    return int(texto.replace(",", "").replace(".", ""))


def lee_log(path: Path) -> tuple[dict[int, Resultado], list[str]]:
    hallados: dict[int, Resultado] = {}
    repetidos: Counter[int] = Counter()
    errores: list[str] = []
    for nlinea, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if "[REPLICA" not in raw:
            continue
        match = LINEA.search(raw)
        if not match:
            errores.append(f"{path.name}:{nlinea}: línea de réplica no interpretable")
            continue
        rep = int(match.group("rep"))
        repetidos[rep] += 1
        try:
            vals = (
                float(match.group("fill")),
                float(numero_entero_agrupado(match.group("backlog"))),
                float(match.group("bw")),
                float(numero_entero_agrupado(match.group("stock"))),
            )
        except ValueError:
            errores.append(f"{path.name}:{nlinea}: valor numérico inválido")
            continue
        if rep not in hallados:
            hallados[rep] = Resultado(rep, vals, nlinea)
    for rep, count in sorted(repetidos.items()):
        if count > 1:
            errores.append(f"{path.name}: réplica #{rep} duplicada ({count} registros)")
    return hallados, errores


def verifica_diseno(path: Path) -> tuple[bool, list[str]]:
    """Revisa las tres variantes de parámetros usadas para generar los logs."""
    texto = path.read_text(encoding="utf-8-sig")
    problemas: list[str] = []
    if not re.search(r"<ModelTimeUnit>(?:<!\[CDATA\[)?Week(?:\]\]>)?</ModelTimeUnit>", texto):
        problemas.append("el modelo no declara la unidad temporal Week")
    nombres = ("ParametersVariation", "ParametersVariation1", "ParametersVariation2")
    bloques: list[str] = []
    for nombre in nombres:
        m = re.search(
            r"<ParamVariationExperiment\b(?:(?!</ParamVariationExperiment>).)*?"
            r"<Name><!\[CDATA\[" + re.escape(nombre) + r"\]\]></Name>"
            r"(?:(?!</ParamVariationExperiment>).)*?</ParamVariationExperiment>",
            texto,
            re.DOTALL,
        )
        if not m:
            problemas.append(f"no se encontró el experimento {nombre}")
            continue
        bloque = m.group(0)
        bloques.append(bloque)
        gen = re.search(r"<CustomGeneratorCode>(.*?)</CustomGeneratorCode>", bloque, re.DOTALL)
        if not gen or gen.group(1).strip() != "new Random(getCurrentReplication())":
            problemas.append(f"{nombre}: generador de semilla no coincide con getCurrentReplication()")
        final = re.search(r"<FinalTime>(.*?)</FinalTime>", bloque)
        final_valor = final.group(1).replace("<![CDATA[", "").replace("]]>", "").strip() if final else ""
        if not final or float(final_valor) != 100.0:
            problemas.append(f"{nombre}: horizonte distinto de 100 semanas")
        rep = re.search(r"<ReplicationPerIteration>(.*?)</ReplicationPerIteration>", bloque)
        if not rep or int(rep.group(1)) != N_ESPERADO:
            problemas.append(f"{nombre}: no declara {N_ESPERADO} réplicas por iteración")
    return not problemas, problemas


def estadistica_pareada(diferencias: list[float]) -> tuple[float, float, float, float, float]:
    n = len(diferencias)
    media = sum(diferencias) / n
    var = sum((x - media) ** 2 for x in diferencias) / (n - 1)
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    margen = T_CRIT_99 * se
    return media, sd, se, media - margen, media + margen


def fmt(x: float) -> str:
    return f"{x:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")


def decimal_csv(texto: str) -> float:
    return float(texto.strip().strip('"').replace(".", "").replace(",", "."))


def audita_csv_intervalos(path: Path, resultados: dict[int, dict[int, Resultado]]) -> tuple[list[str], bool]:
    """Compara las cuatro filas CRN guardadas contra diferencias calculadas desde logs."""
    if not path.is_file() or len(resultados) != 3:
        return ["No disponible: falta el CSV o los tres logs."], False
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    crn_rows = [r for r in rows if r and r[0].strip() == "Escenario 2 vs Escenario 0"]
    esperado = {
        "Delta Fill Rate Global": 0,
        "Delta Backlog Promedio": 1,
        "Delta Razón Bullwhip": 2,
        "Delta Stock en Depósito": 3,
    }
    lines: list[str] = []
    valid = len(crn_rows) == len(esperado)
    if not valid:
        lines.append(f"Se encontraron {len(crn_rows)} filas CRN (se esperaban {len(esperado)}).")
    vistas: set[str] = set()
    for row in crn_rows:
        if len(row) < 10:
            valid = False
            lines.append("Fila CRN con columnas incompletas.")
            continue
        kpi_nombre = row[1].strip().split(" (", 1)[0]
        idx = esperado.get(kpi_nombre)
        if idx is None:
            valid = False
            lines.append(f"KPI CRN desconocido: {row[1]}")
            continue
        vistas.add(kpi_nombre)
        diffs = [resultados[2][i].valores[idx] - resultados[0][i].valores[idx] for i in range(1, N_ESPERADO + 1)]
        mean, sd, se, lo, hi = estadistica_pareada(diffs)
        # El CSV conserva dos decimales en las seis estadísticas contrastadas.
        actual = [decimal_csv(row[i]) for i in (3, 4, 5, 6, 7, 8)]
        expected = [mean, sd, se, T_CRIT_99 * se, lo, hi]
        nombres = ("media", "DE", "EE", "margen", "límite inferior", "límite superior")
        discrepancias = [abs(a - b) for a, b in zip(actual, expected)]
        tolerancias = [0.5 * (10 ** -len(row[i].split(",", 1)[1])) if "," in row[i] else 1.0000001 for i in (3, 4, 5, 6, 7, 8)]
        row_ok = all(delta <= tol + 1e-9 for delta, tol in zip(discrepancias, tolerancias))
        valid = valid and row_ok
        if row_ok:
            msg = "coincide con los logs al redondeo publicado"
            if any(d > 0.5 and "," not in row[i] for d, i in zip(discrepancias, (3, 4, 5, 6, 7, 8))):
                msg += "; el margen de error está truncado con diferencia menor a 1 unidad"
            lines.append(f"- {row[1]}: {msg}")
        else:
            lines.append(f"- {row[1]}: NO coincide; " + ", ".join(f"{n}: diferencia {fmt(d)}" for n, d in zip(nombres, discrepancias)))
    if vistas != set(esperado):
        valid = False
        lines.append("Faltan KPIs en el bloque pareado del CSV.")
    return lines, valid


def ejecuta(root: Path, report_path: Path) -> tuple[int, str]:
    logs = {s: root / "csv" / f"esc{s}.txt" for s in range(3)}
    model = root / "main_con_3d" / "Domitec_Main_3D.alp"
    autosave = root / "Domitec_planta_produccion_simulada_3.alp.autosave"
    all_errors: list[str] = []
    resultados: dict[int, dict[int, Resultado]] = {}
    for s, path in logs.items():
        if not path.is_file():
            all_errors.append(f"Falta el log {path}")
            continue
        registros, errores = lee_log(path)
        resultados[s] = registros
        all_errors.extend(errores)
        ids = set(registros)
        faltan = sorted(set(range(1, N_ESPERADO + 1)) - ids)
        extra = sorted(ids - set(range(1, N_ESPERADO + 1)))
        if faltan:
            all_errors.append(f"{path.name}: faltan réplicas {faltan}")
        if extra:
            all_errors.append(f"{path.name}: réplicas fuera de 1..{N_ESPERADO}: {extra}")
    diseno_ok = True
    for source in (model, autosave):
        if not source.is_file():
            all_errors.append(f"Falta la evidencia del modelo {source}")
            diseno_ok = False
            continue
        ok, motivos = verifica_diseno(source)
        diseno_ok = diseno_ok and ok
        all_errors.extend(f"{source.name}: {motivo}" for motivo in motivos)
    if len(resultados) == 3:
        for a, b in PARES:
            faltan_a = sorted(set(resultados[a]) - set(resultados[b]))
            faltan_b = sorted(set(resultados[b]) - set(resultados[a]))
            if faltan_a or faltan_b:
                all_errors.append(f"Esc{a}/Esc{b}: IDs no emparejables; solo Esc{a}={faltan_a}, solo Esc{b}={faltan_b}")

    datos_ok = len(resultados) == 3 and not any(
        "Falta el log" in e or "duplicada" in e or "no interpretable" in e or
        "faltan réplicas" in e or "fuera de 1.." in e or "IDs no emparejables" in e
        for e in all_errors
    )
    estimables = datos_ok and diseno_ok
    lines = [
        "# Auditoría estadística de comparación por réplica",
        "",
        "## Evidencia de entrada",
        "",
        "Se leyeron los tres logs de `csv/esc{0,1,2}.txt`. Los registros contienen KPIs finales por réplica (Fill Rate, backlog, razón BW y stock), pero no series temporales semanales ni una columna de semilla emitida en tiempo de ejecución.",
        "",
    ]
    for s, registro in sorted(resultados.items()):
        ids = sorted(registro)
        lines.append(f"- `esc{s}.txt`: {len(ids)} registros únicos; rango {ids[0]}–{ids[-1]}" if ids else f"- `esc{s}.txt`: sin registros interpretables")
    lines += ["", "### Integridad y semillas", ""]
    if diseno_ok:
        lines.append("`main_con_3d/Domitec_Main_3D.alp` y el autosave `Domitec_planta_produccion_simulada_3.alp.autosave` muestran en las tres variantes `ParametersVariation{,1,2}` `new Random(getCurrentReplication())`, 100 réplicas por iteración y tiempo final 100 con unidad `Week`. Esto verifica la configuración guardada: la semilla prevista es el ID de réplica en las tres variantes. Los logs no registran semilla ni identifican de manera inequívoca el archivo/versionado con que se generaron. La igualdad efectiva de semillas para estas corridas históricas no se puede verificar solo con los logs; por eso los IC siguientes son condicionales a que procedan de estas variantes y configuración. Los experimentos `Simulation_Escenario*` de ejecución interactiva usan `randomSeed` y no verifican semillas comunes.")
    else:
        lines.append("No se pudo verificar el diseño de semilla común y horizonte de 100 semanas en el modelo; se rechaza la inferencia pareada.")
    if all_errors:
        lines += ["", "Hallazgos que impiden o limitan el cálculo:", ""]
        lines.extend(f"- {x}" for x in all_errors)
    csv_audit, csv_ok = audita_csv_intervalos(root / "csv" / "resultados corridas - Intervalos_Confianza.csv", resultados)
    lines += ["", "## Comparación pareada", ""]
    if estimables:
        lines += [
            "Emparejamiento por el ID `[REPLICA #n]`; diferencia definida como primer escenario menos segundo escenario. Se usa t de Student con `n=100`, `gl=99`, `t crítico=1,9842169515`; IC bilateral del 95%: media de diferencias ± t·s/√n. Los cálculos son descriptivos y condicionales a la configuración de semillas indicada arriba.",
            "",
            "| Contraste | KPI | n | Media de diferencias | DE diferencias | EE | IC 95% inferior | IC 95% superior |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for a, b in PARES:
            for k, name in enumerate(KPI):
                diffs = [resultados[a][i].valores[k] - resultados[b][i].valores[k] for i in range(1, N_ESPERADO + 1)]
                mean, sd, se, lo, hi = estadistica_pareada(diffs)
                lines.append(f"| Esc{a} − Esc{b} | {name} | {N_ESPERADO} | {fmt(mean)} | {fmt(sd)} | {fmt(se)} | {fmt(lo)} | {fmt(hi)} |")
    else:
        lines.append("Cálculo rechazado: faltan registros completos y únicos por réplica o evidencia de configuración de semilla común. No se calculan IC pareados.")
    lines += [
        "",
        "## Welch y estacionariedad",
        "",
        "No se ejecutaron pruebas de Welch ni de estacionariedad. Las entradas disponibles son métricas finales agregadas por corrida, no 100 series observacionales semanales por escenario. El horizonte de 100 semanas se confirma en la configuración, pero no sustituye las observaciones temporales requeridas para esas comprobaciones.",
        "",
        "## CSV existentes",
        "",
        "`resultados corridas - Registro_Corridas.csv` contiene 300 filas: 100 por escenario, con IDs 1–100 reiniciados dentro de cada escenario. La columna “Semilla / Réplica” solo etiqueta la réplica, no reporta la semilla. El CSV de intervalos tiene 12 filas de IC marginales y cuatro filas CRN para Escenario 2 − Escenario 0.",
        "",
        "Auditoría numérica del bloque CRN del CSV contra las diferencias recalculadas desde `esc0.txt` y `esc2.txt` por ID de réplica:",
        "",
        *csv_audit,
        "",
        ("Los cuatro contrastes del CSV reproducen el cálculo por ID de réplica, con la precisión publicada; la igualdad de semillas/flujos de demanda históricos sigue sin verificarse. La etiqueta CRN no prueba por sí sola que las corridas históricas compartieran demanda." if csv_ok else "El bloque CRN del CSV no queda validado frente a los logs."),
        "",
        "## Recomendación sobre AnyLogic",
        "",
        "Los tres experimentos guardados por separado no conforman un runner que itere explícitamente por réplica y escenario. Para un runner de 300 corridas, ejecutar secuencialmente `replica=1..100` y, dentro de cada réplica, escenarios 0, 1 y 2; registrar en cada resultado `replica`, `seed`, escenario, inicio/fin y KPIs. Usar el mismo valor de semilla no garantiza la misma demanda aleatoria si los escenarios consumen el generador compartido en distinto orden o cantidad; separar los flujos aleatorios de demanda de los flujos propios de cada escenario y alimentar demanda con un stream identificado por réplica. Conservar series semanales para warm-up/estacionariedad; no descartar un warm-up fijo sin diagnosticar las series y definir el estimando (horizonte finito vs. estado estable). En la interfaz, exponer cantidad de réplicas, semilla base, duración en semanas, estado/progreso, exportación de datos y KPI/IC pareados; dejar explícito que el pareamiento por semillas requiere flujos comunes, no solo el mismo seed del motor.",
        "",
    ]
    report = "\n".join(lines)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return (0 if estimables else 2), report


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="raíz del repositorio")
    parser.add_argument("--report", type=Path, default=None, help="ruta del reporte Markdown")
    args = parser.parse_args()
    report_path = args.report or (Path(__file__).resolve().parent / "auditoria_estadistica.md")
    code, report = ejecuta(args.root.resolve(), report_path.resolve())
    print(report)
    print(f"\nReporte escrito: {report_path.resolve()}")
    return code


if __name__ == "__main__":
    sys.exit(main())
