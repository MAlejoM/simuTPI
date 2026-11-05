# Auditoría estadística de comparación por réplica

## Evidencia de entrada

Se leyeron los tres logs de `csv/esc{0,1,2}.txt`. Los registros contienen KPIs finales por réplica (Fill Rate, backlog, razón BW y stock), pero no series temporales semanales ni una columna de semilla emitida en tiempo de ejecución.

- `esc0.txt`: 100 registros únicos; rango 1–100
- `esc1.txt`: 100 registros únicos; rango 1–100
- `esc2.txt`: 100 registros únicos; rango 1–100

### Integridad y semillas

`main_con_3d/Domitec_Main_3D.alp` y el autosave `Domitec_planta_produccion_simulada_3.alp.autosave` muestran en las tres variantes `ParametersVariation{,1,2}` `new Random(getCurrentReplication())`, 100 réplicas por iteración y tiempo final 100 con unidad `Week`. Esto verifica la configuración guardada: la semilla prevista es el ID de réplica en las tres variantes. Los logs no registran semilla ni identifican de manera inequívoca el archivo/versionado con que se generaron. La igualdad efectiva de semillas para estas corridas históricas no se puede verificar solo con los logs; por eso los IC siguientes son condicionales a que procedan de estas variantes y configuración. Los experimentos `Simulation_Escenario*` de ejecución interactiva usan `randomSeed` y no verifican semillas comunes.

## Comparación pareada

Emparejamiento por el ID `[REPLICA #n]`; diferencia definida como primer escenario menos segundo escenario. Se usa t de Student con `n=100`, `gl=99`, `t crítico=1,9842169515`; IC bilateral del 95%: media de diferencias ± t·s/√n. Los cálculos son descriptivos y condicionales a la configuración de semillas indicada arriba.

| Contraste | KPI | n | Media de diferencias | DE diferencias | EE | IC 95% inferior | IC 95% superior |
|---|---|---:|---:|---:|---:|---:|---:|
| Esc0 − Esc1 | Fill Rate (%) | 100 | 0,0713 | 2,2555 | 0,2255 | -0,3762 | 0,5188 |
| Esc0 − Esc1 | Backlog (cajas) | 100 | -6.593,1400 | 196.600,0578 | 19.660,0058 | -45.602,8567 | 32.416,5767 |
| Esc0 − Esc1 | Razón BW | 100 | 0,6957 | 0,1745 | 0,0174 | 0,6611 | 0,7303 |
| Esc0 − Esc1 | Stock depósito (cajas) | 100 | 1.496,3900 | 8.963,3408 | 896,3341 | -282,1313 | 3.274,9113 |
| Esc0 − Esc2 | Fill Rate (%) | 100 | -9,6856 | 1,8624 | 0,1862 | -10,0552 | -9,3160 |
| Esc0 − Esc2 | Backlog (cajas) | 100 | 729.810,1800 | 159.371,0367 | 15.937,1037 | 698.187,5087 | 761.432,8513 |
| Esc0 − Esc2 | Razón BW | 100 | 0,6915 | 0,1705 | 0,0170 | 0,6577 | 0,7253 |
| Esc0 − Esc2 | Stock depósito (cajas) | 100 | -8.072,2700 | 17.188,3903 | 1.718,8390 | -11.482,8195 | -4.661,7205 |
| Esc1 − Esc2 | Fill Rate (%) | 100 | -9,7569 | 1,6861 | 0,1686 | -10,0915 | -9,4223 |
| Esc1 − Esc2 | Backlog (cajas) | 100 | 736.403,3200 | 144.932,4388 | 14.493,2439 | 707.645,5798 | 765.161,0602 |
| Esc1 − Esc2 | Razón BW | 100 | -0,0042 | 0,0749 | 0,0075 | -0,0191 | 0,0107 |
| Esc1 − Esc2 | Stock depósito (cajas) | 100 | -9.568,6600 | 15.468,0902 | 1.546,8090 | -12.637,8647 | -6.499,4553 |

## Welch y estacionariedad

No se ejecutaron pruebas de Welch ni de estacionariedad. Las entradas disponibles son métricas finales agregadas por corrida, no 100 series observacionales semanales por escenario. El horizonte de 100 semanas se confirma en la configuración, pero no sustituye las observaciones temporales requeridas para esas comprobaciones.

## CSV existentes

`resultados corridas - Registro_Corridas.csv` contiene 300 filas: 100 por escenario, con IDs 1–100 reiniciados dentro de cada escenario. La columna “Semilla / Réplica” solo etiqueta la réplica, no reporta la semilla. El CSV de intervalos tiene 12 filas de IC marginales y cuatro filas CRN para Escenario 2 − Escenario 0.

Auditoría numérica del bloque CRN del CSV contra las diferencias recalculadas desde `esc0.txt` y `esc2.txt` por ID de réplica:

- Delta Fill Rate Global: coincide con los logs al redondeo publicado
- Delta Backlog Promedio: coincide con los logs al redondeo publicado; el margen de error está truncado con diferencia menor a 1 unidad
- Delta Razón Bullwhip: coincide con los logs al redondeo publicado
- Delta Stock en Depósito: coincide con los logs al redondeo publicado

Los cuatro contrastes del CSV reproducen el cálculo por ID de réplica, con la precisión publicada; la igualdad de semillas/flujos de demanda históricos sigue sin verificarse. La etiqueta CRN no prueba por sí sola que las corridas históricas compartieran demanda.

## Recomendación sobre AnyLogic

Los tres experimentos guardados por separado no conforman un runner que itere explícitamente por réplica y escenario. Para un runner de 300 corridas, ejecutar secuencialmente `replica=1..100` y, dentro de cada réplica, escenarios 0, 1 y 2; registrar en cada resultado `replica`, `seed`, escenario, inicio/fin y KPIs. Usar el mismo valor de semilla no garantiza la misma demanda aleatoria si los escenarios consumen el generador compartido en distinto orden o cantidad; separar los flujos aleatorios de demanda de los flujos propios de cada escenario y alimentar demanda con un stream identificado por réplica. Conservar series semanales para warm-up/estacionariedad; no descartar un warm-up fijo sin diagnosticar las series y definir el estimando (horizonte finito vs. estado estable). En la interfaz, exponer cantidad de réplicas, semilla base, duración en semanas, estado/progreso, exportación de datos y KPI/IC pareados; dejar explícito que el pareamiento por semillas requiere flujos comunes, no solo el mismo seed del motor.
