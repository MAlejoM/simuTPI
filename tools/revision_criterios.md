# Revisión de criterios del experimento Domitec

**Versión operativa actual: `operacion-24x7-v2`.** Se corrigieron calendario,
cancelaciones, demanda y liberación de material. La auditoría 100×3 descrita debajo
corresponde a la versión anterior y no acredita resultados del modelo corregido.
La nueva ejecución nativa y su calibración están pendientes. Ver
[`solucion_operativa_24x7.md`](../docs/solucion_operativa_24x7.md).

## Alcance y estado

Esta revisión separa el snapshot histórico de la implementación experimental nueva. Los logs `csv/esc0.txt`, `esc1.txt` y `esc2.txt` contienen 100 registros únicos por escenario, numerados del 1 al 100. El CSV histórico ya incluía intervalos marginales y un bloque de comparación pareada 2–0. Los identificadores de réplica permiten reproducir sus diferencias por ID, pero los logs y la columna “Semilla / Réplica” no guardan la semilla efectiva: ese snapshot no prueba que la demanda se haya compartido entre escenarios.

El nuevo lote `comparacion_20261106_002510_679` se publicó correctamente y fue auditado sin volver a ejecutar el modelo. Contiene 300 resultados, 30.000 observaciones semanales, 15 IC y marcador `COMPLETO`. La revisión numérica está en [auditoria_estudio_real.md](auditoria_estudio_real.md) y las huellas de sus archivos en [auditoria_estudio_real.json](auditoria_estudio_real.json). Los valores históricos de `main.tex` no se atribuyen a esta implementación.

## Matriz de criterios

| Criterio | Código o evidencia disponible | Estado | Pendiente para cerrar |
|---|---|---|---|
| Diseño PLE: 100 iteraciones × 3 réplicas, semilla `i` y escenario `r-1` | Experimento nativo de variación de parámetros; salida con semillas 1–100 y exactamente tres escenarios por semilla | Verificado en el lote exportado | Conservar el paquete y sus huellas junto al informe final. |
| CRN de demanda común independiente del orden de sorteos | Generador por clave; firmas iguales por semilla y demanda semanal idéntica en las 10.000 ternas semilla×semana | Verificado en código y salida | El mismo seed del motor por sí solo no basta; conservar también firmas y series. |
| Firma verificable de las 1.800 entradas | La validación nativa exige 1.800 claves por corrida antes de publicar; el CSV conserva SHA-256 común a cada terna | 100 ternas verificadas | Mantener la validación estricta al modificar la demanda. |
| Horizonte y series semanales completas | 300 grupos de 100 semanas 0–99; horizonte del experimento 100 y observación de estado en `k + 0,9999` | Verificado en código y salida | El estado se toma cerca del cierre semanal, separado de la tolerancia del evento de fin. |
| Fill Rate por cohortes y warm-up | `ConfiguracionDomitec.calentamiento` es editable; la UI propone 15 semanas; el cálculo filtra pedidos por tiempo de entrada | Warm-up de 15 semanas provisional | Ejecutar sensibilidad a otros cortes; no tratar 15 semanas como warm-up validado ni como evidencia de estado estacionario. |
| IC pareados para tres parejas y cinco métricas | Recalculados desde los 300 resultados; coinciden media, desviación, SEM y límites con `n=100`, `gl=99`, `t=1,9842169515` | Los 15 IC coinciden | No forzar exclusión de cero: los escenarios 1 y 2 coinciden exactamente en este lote. |
| Exportación auditable | Carpeta única con cuatro archivos de datos/metadatos y marcador `COMPLETO`; sin renombrado ni borrado ante fallos | Publicación nativa y carga verificadas | Conservar el paquete original sin sobrescribirlo. |
| Interfaz durante una comparación | Comparación directa con valores predeterminados o configuración guardada opcional; progreso y reintento de guardado. Main permite leer los IC publicados. | Exportación nativa auditada; acciones y persistencia compiladas | Revisar visualmente la nueva guía de nueve sectores y su navegación; no altera la lógica del estudio. |
| Pruebas de integración y corrida 100×3 | Compilación de acciones, pruebas Java y paquete real revisado | Lote completo y exportación auditados | La nueva guía visual se comprueba aparte; no modifica los cálculos del lote. |
| Estacionariedad | Diagnóstico descriptivo ejecutado con las series reales: medias por semana, suavizado Welch y pendientes | **No demostrado formalmente** | Validar warm-up y sensibilidad; una pendiente descriptiva no equivale a prueba formal de estacionariedad. |

## Observaciones de auditoría histórica

- Los intervalos pareados 2–0 del CSV existente reproducen diferencias calculadas desde los logs por ID de réplica, dentro del redondeo publicado. Ese ajuste numérico valida el emparejamiento por etiqueta, no la igualdad de semillas o de la demanda histórica.
- Los resultados de la tabla histórica en `main.tex` pertenecen al snapshot anterior. No son resultados de las nuevas firmas, del nuevo warm-up ni de la implementación PLE.
- La configuración As-Is puede tener capacidad efectiva menor que la demanda atendida y producir backlog creciente; la censura de entregas también puede afectar los indicadores. Es una hipótesis a revisar en series semanales, no una tendencia probada estadísticamente ni un resultado de las 300 subcorridas.
- No se descarta warm-up como estado estacionario validado: 15 semanas es un valor inicial editable. La evidencia de estacionariedad requiere los datos semanales nativos y análisis adicional.
