# Diagnóstico de datos operativos

Generado por `tools/analizar_datos_operativos.py`. Los CSV fuente se leen sin modificarlos.

## Alcance y calidad

- Demanda: 23,689 registros con año; se excluyeron 1 fila(s) de resumen `Total`.
- Ecuación Pedidos = Despachadas + Cancelado + Pendientes: 0 discrepancias.
- Duplicados por año, negocio, mes, cliente, rubro y presentación: 0.
- Las unidades de demanda no están declaradas. Producción no tiene año; sus totales no son directamente comparables con los años de demanda.
- `prod.csv` es la fuente principal; `prod1.csv` es variante/subconjunto y no se suma. Septiembre de `prod.csv` se excluye de tasas por aparente parcialidad.
- La familia Lavandina combina común y concentrada, pero se asigna a una sola línea/rate `lavandina` de `prod3.csv`.
- Se excluyen de las seis familias comparables: PROMOPACK, LÍQUIDO LIMPIADOR y LÍQUIDO BACTERICIDA.

## Demanda anual

| Año | Pedidos | Despachadas | Cancelado | Pendientes |
|---:|---:|---:|---:|---:|
| 2025 | 3,242,281 | 2,977,002 | 265,279 | 0 |
| 2026 | 2,611,314 | 2,041,048 | 324,232 | 246,034 |

## Tasa observada para calibración (prod.csv, ene–ago)

`Tiempo` se interpreta provisionalmente como minutos. Tasa observada = suma Cajas / (suma Tiempo / 60). La producción no tiene año.

| Familia | Rubros incluidos | Cajas ene–ago | Cajas/h observado* | Prod/Hs/Ho prom. | Operarios prom. | (Prod/Hs/Ho × Operarios), ponderado por tiempo | prod3 nominal/h | prod3 h/mes | prod3 capacidad/mes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Desinfectante | LIQUIDO DESINFECTANTE | 426,507 | 185.22 | 49.56 | 3.92 | 185.51 | 205.00 | 330.00 | 67,650 |
| Detergente concentrado | DETERGENTE CONCENTRADO | 86,900 | 110.41 | 27.85 | 4.00 | 110.71 | 110.00 | — | — |
| Lavandina | LAVANDINA COMUN, LAVANDINA CONCENTRADA | 943,087 | 226.25 | 42.75 | 4.78 | 226.07 | 235.00 | 330.00 | 77,550 |
| Lavarropa | LIQUIDO LAVAR ROPA | 231,640 | 109.06 | 35.74 | 3.05 | 109.18 | 120.00 | 330.00 | 39,600 |
| Lavavajilla | LAVAVAJILLA | 470,742 | 224.52 | 57.75 | 3.88 | 225.97 | 236.00 | 330.00 | 77,880 |
| Suavizante | SUAVIZANTE | 132,007 | 62.75 | 31.59 | 2.69 | 62.76 | 60.00 | 330.00 | 19,800 |

* Lavandina es una única línea: tasa pooled común + concentrada = **226.255 cajas/h**; producción acumulada ene–ago = **943087 cajas**, suma de Tiempo = **250095 min** (521.0 h/mes promedio si Tiempo está en minutos). Capacidad nominal prod3 = **77550 cajas/mes** (235 × 330), una línea; no se duplica por tener dos rubros.

`Prod/Hs/Ho` parece una tasa por operario: en el primer renglón de prod.csv, 3,499 / (1,790/60) = 117.3 cajas/h de línea; dividido por 4 operarios = 29.3, coincidente con Prod/Hs/Ho=29. En los agregados se muestra la comparación como contraste de etiqueta, no como definición confirmada.

## Demanda por mes

Los totales completos por año/mes, por rubro y por canal de seis familias están en el JSON adjunto; se mantienen allí para evitar una tabla extensa en este resumen.

## Fuentes y huellas SHA-256

| Fuente | SHA-256 |
|---|---|
| `demanda/demanda - Sheet1.csv` | `b69030917f619ead3590753f8ff0936ede66383b4c782cbae5467dece11e72a6` |
| `produccion/prod.csv` | `0bef94aecae58caba72e9c4c956129bcdd7e5dcef0d54cb760537611b0ee03d8` |
| `produccion/prod1.csv` | `3ffd6a772b283aaf3034b514062c63f06889e8cd77039e46ce984a764d0a3fd6` |
| `produccion/prod3.csv` | `bfdc98a17ff79762deae95a0b0e5d907f8f3191ed6c65c3a2cc14884a55863eb` |
