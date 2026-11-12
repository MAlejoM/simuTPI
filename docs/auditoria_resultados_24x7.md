# Auditoría de resultados de operación 24x7

**Paquete:** domitec_interactivo/resultados_operativos_v2/comparacion_20261111_194531_208  
**Modelo:** operacion-24x7-v2; AnyLogic 8.9.10. Horizonte 100 semanas, calentamiento 15 semanas; escenarios hipotéticos y supuestos de modelo, no validación en planta.

## Integridad del paquete

- Corridas: 300; escenario 0/1/2: 100/100/100; semillas exactamente 1–100 por escenario: true; claves semilla/escenario únicas: 300.
- Series semanales: 30000; por escenario 10000/10000/10000; claves semilla/escenario/semana únicas: 30000.
- CRN: firma SHA-256 única por semilla compartida entre escenarios: true; demandas semanales idénticas en 10.000 ternas (seed, semana; cada terna compara 3 filas, 30.000 valores de escenario): 0 discrepancias.
- IC pareados: 15 filas existentes (15 esperadas). Recalculé por semilla los cinco indicadores del CSV y tres métricas adicionales; t crítico 1,9842169515, n=100, gl=99. Máxima discrepancia de media o límite frente al CSV: 0.000e+0.
- WIP máximo registrado: 35.000 cajas; límite configurado 36.000 cajas (36 lotes × 1.000): true.

### SHA-256

| Archivo | SHA-256 |
|---|---|
| COMPLETO | 1378691549409c7049d257c97d058cb1a6f038fdd8d62244f99bf3d1361680dd |
| metadata.txt | ca225bfb93a7e9a0301f07977047dfe7d289b581e890d17dec77065ac00bf9bb |
| resultados.csv | c4b6a76d276db452b5140aaac157885fab83802ba735888d408b8d40074814b9 |
| ic_pareados.csv | 58c51cd2d3891ec5376f362b64e2f7d014034181d083af06c55445cfd6cb70dc |
| series_semanales.csv | f6eed051cef44d33bba0c1573303c2253b92ab8896960ae4d79e753dd463d447 |

## Resumen marginal por escenario

Media y desviación estándar muestral entre 100 réplicas; cada columna es una métrica independiente.

| Métrica | Esc. 0 media (DE) | Esc. 1 media (DE) | Esc. 2 media (DE) |
|---|---:|---:|---:|
| Fill rate (%) | 96,11 (1,77) | 96,12 (1,77) | 99,72 (0,40) |
| Backlog final (cajas) | 50.687,79 (27.706,71) | 50.881,43 (28.003,70) | 10.841,52 (16.931,08) |
| Stock final (cajas) | 45.777,65 (27.873,17) | 43.405,73 (27.655,80) | 63.544,44 (34.617,11) |
| Efecto látigo | 1,81 (0,23) | 1,13 (0,10) | 1,01 (0,02) |
| Producción (cajas) | 4.663.840,00 (130.613,60) | 4.664.660,00 (130.718,24) | 4.836.350,00 (181.795,94) |
| Cancelaciones (cajas) | 140.827,15 (84.898,67) | 140.081,59 (84.722,59) | 3.268,40 (10.134,32) |
| WIP máximo (cajas) | 33.090,00 (683,06) | 31.650,00 (609,27) | 26.440,00 (591,52) |
| Insumos finales (cajas equiv.) | 83.960,00 (34.445,95) | 74.120,00 (30.271,26) | 14.880,00 (18.036,60) |

## Diferencias pareadas e IC del 95%

Diferencia = escenario a − escenario b; IC t bilateral pareado por semilla, n=100 y gl=99.

| a−b | Métrica | Media dif. | IC 95% |
|---|---|---:|---:|
| 0−1 | Fill rate (%) | -0,01 | [-0,02, -0,01] |
| 0−1 | Backlog final (cajas) | -193,64 | [-408,73, 21,45] |
| 0−1 | Stock final (cajas) | 2.371,92 | [1.808,98, 2.934,86] |
| 0−1 | Efecto látigo | 0,68 | [0,64, 0,71] |
| 0−1 | Producción (cajas) | -820,00 | [-1.691,26, 51,26] |
| 0−1 | Cancelaciones (cajas) | 745,56 | [558,83, 932,29] |
| 0−1 | WIP máximo (cajas) | 1.440,00 | [1.292,59, 1.587,41] |
| 0−1 | Insumos finales (cajas equiv.) | 9.840,00 | [8.561,61, 11.118,39] |
| 0−2 | Fill rate (%) | -3,61 | [-3,92, -3,30] |
| 0−2 | Backlog final (cajas) | 39.846,27 | [36.164,84, 43.527,70] |
| 0−2 | Stock final (cajas) | -17.766,79 | [-20.441,45, -15.092,13] |
| 0−2 | Efecto látigo | 0,79 | [0,74, 0,84] |
| 0−2 | Producción (cajas) | -172.510,00 | [-187.935,09, -157.084,91] |
| 0−2 | Cancelaciones (cajas) | 137.558,75 | [121.659,11, 153.458,39] |
| 0−2 | WIP máximo (cajas) | 6.650,00 | [6.477,58, 6.822,42] |
| 0−2 | Insumos finales (cajas equiv.) | 69.080,00 | [64.110,71, 74.049,29] |
| 1−2 | Fill rate (%) | -3,60 | [-3,91, -3,29] |
| 1−2 | Backlog final (cajas) | 40.039,91 | [36.326,75, 43.753,07] |
| 1−2 | Stock final (cajas) | -20.138,71 | [-22.754,64, -17.522,78] |
| 1−2 | Efecto látigo | 0,11 | [0,09, 0,13] |
| 1−2 | Producción (cajas) | -171.690,00 | [-187.034,50, -156.345,50] |
| 1−2 | Cancelaciones (cajas) | 136.813,19 | [120.949,10, 152.677,28] |
| 1−2 | WIP máximo (cajas) | 5.210,00 | [5.054,77, 5.365,23] |
| 1−2 | Insumos finales (cajas equiv.) | 59.240,00 | [55.125,04, 63.354,96] |

## Evolución temporal descriptiva

Promedios de la serie semanal agrupados entre réplicas por ventanas 15–29, 85–99 y 20–99. En backlog, la media aumenta entre ventanas en los tres escenarios (esc. 0: 27.468 a 49.267; esc. 1: 27.585 a 49.461; esc. 2: 6.163 a 9.544 cajas), y las pendientes descriptivas 20–99 son positivas. Esto describe la trayectoria finita observada y no constituye una prueba de no estacionariedad. Pendientes son regresiones lineales descriptivas por semana sobre semanas 20–99.

| Esc. | Métrica | Sem. 15–29 | Sem. 85–99 | Sem. 20–99 | Pendiente/sem. 20–99 |
|---:|---|---:|---:|---:|---:|
| 0 | demanda | 57.433,40 | 57.671,23 | 57.113,48 | 3,231 |
| 0 | ordenes | 56.814,00 | 55.674,00 | 55.405,38 | -7,316 |
| 0 | produccion | 54.510,00 | 55.074,00 | 54.927,13 | 0,850 |
| 0 | stock | 52.173,12 | 45.591,26 | 48.076,90 | -60,284 |
| 0 | backlog | 27.468,14 | 49.266,59 | 41.811,52 | 222,187 |
| 0 | wip | 16.760,00 | 18.260,00 | 17.947,88 | 10,325 |
| 1 | demanda | 57.433,40 | 57.671,23 | 57.113,48 | 3,231 |
| 1 | ordenes | 56.629,33 | 55.529,33 | 55.402,50 | -9,610 |
| 1 | produccion | 54.538,67 | 55.084,00 | 54.926,38 | 1,002 |
| 1 | stock | 50.265,82 | 43.546,52 | 45.949,56 | -58,507 |
| 1 | backlog | 27.585,31 | 49.460,72 | 41.930,62 | 222,889 |
| 1 | wip | 15.887,33 | 17.628,00 | 17.221,38 | 13,704 |
| 2 | demanda | 57.433,40 | 57.671,23 | 57.113,48 | 3,231 |
| 2 | ordenes | 57.426,67 | 57.615,33 | 57.074,38 | 2,950 |
| 2 | produccion | 56.676,67 | 57.312,00 | 56.946,13 | 0,701 |
| 2 | stock | 67.235,34 | 64.679,08 | 66.643,19 | -14,202 |
| 2 | backlog | 6.162,91 | 9.544,11 | 8.114,66 | 30,855 |
| 2 | wip | 6.779,33 | 7.417,33 | 7.105,13 | 3,669 |

## Interpretación y límites

El paquete supera los chequeos estructurales de filas, semillas, réplicas, firmas CRN, igualdad de demanda semanal y límites de WIP. Los IC de diferencias son contrastes pareados por semilla. Las ventanas temporales y pendientes describen tendencias y no demuestran estacionariedad. Cancelaciones, espera de pedidos y reglas de capacidad por escenario son supuestos del modelo; los resultados no equivalen a estimaciones verificadas en planta.


