# Auditoría de paquete exportado

Paquete auditado: `domitec_interactivo/resultados_domitec/comparacion_20261106_002510_679`  
No se ejecutaron corridas ni se modificaron los CSV.

## Integridad estructural

- Están presentes los cinco archivos esperados: `resultados.csv`, `series_semanales.csv`, `ic_pareados.csv`, `metadata.txt` y `COMPLETO`.
- El marcador contiene `run_id=20261106_002510_679`.
- `resultados.csv`: 300 filas de datos; semillas 1–100, exactamente 3 escenarios (0, 1, 2) por semilla. Las 100 semillas tienen una firma SHA-256 de demanda válida y común a sus tres escenarios.
- `series_semanales.csv`: 30.000 filas de datos distribuidas en 300 grupos semilla×escenario; cada grupo tiene exactamente las semanas 0–99.
- `ic_pareados.csv`: 15 contrastes, todos con n=100 y df=99. Recalculé desde `resultados.csv` las diferencias pareadas escenario_a menos escenario_b, la media, desviación muestral, error estándar y el IC t bilateral al 95%; los 15 resultados coinciden con el CSV publicado (t crítico 1,9842169515; tolerancia numérica relativa 1e-8).

## Intervalos pareados recalculados

IC del 95% para la diferencia `escenario_a - escenario_b`:

| Par | Métrica | Media | IC 95% | Incluye 0 |
|---|---|---:|---:|:---:|
| 0–1 | fillRate | 0,04128 | [0,03214; 0,05042] | No |
| 0–1 | backlog | −2613,91 | [−3189,74; −2038,08] | No |
| 0–1 | stock | 9626,09 | [8176,96; 11075,22] | No |
| 0–1 | bw | 0,52048 | [0,49149; 0,54946] | No |
| 0–1 | producción | 580,00 | [−1623,43; 2783,43] | Sí |
| 0–2 | fillRate | 0,04128 | [0,03214; 0,05042] | No |
| 0–2 | backlog | −2613,91 | [−3189,74; −2038,08] | No |
| 0–2 | stock | 9626,09 | [8176,96; 11075,22] | No |
| 0–2 | bw | 0,52048 | [0,49149; 0,54946] | No |
| 0–2 | producción | 580,00 | [−1623,43; 2783,43] | Sí |
| 1–2 | fillRate | 0 | [0; 0] | Sí |
| 1–2 | backlog | 0 | [0; 0] | Sí |
| 1–2 | stock | 0 | [0; 0] | Sí |
| 1–2 | bw | 0 | [0; 0] | Sí |
| 1–2 | producción | 0 | [0; 0] | Sí |

Las observaciones de escenarios 1 y 2 coinciden para las cinco métricas en las 100 semillas, por eso sus diferencias pareadas e intervalos son exactamente cero. Los intervalos de producción de 0–1 y 0–2 sí incluyen cero. Esto resume los resultados finitos de estas 100 semillas; no constituye una prueba formal de estacionariedad.
