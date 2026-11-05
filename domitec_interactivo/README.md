# Domitec interactivo

Abrir `Domitec_Interactivo.alp` en AnyLogic 8.9.10 PLE. Para recorrer la interfaz,
ejecutar `Simulation_Escenario0_AsIs`: las pestañas son Vista 2D, Vista 3D,
Estadísticas y Lógica. Los parámetros se editan en Lógica y se confirman con
los botones de aplicar. Los lotes que ya están procesándose conservan su tiempo.

La vista 2D es un esquema de flujo por producto, con lotes reales por etapa,
stock y backlog. La pestaña 3D muestra la geometría de la planta. Los elementos
de programación están fuera del panel en el editor y ocultos en la ejecución.
La primera entrega ya no cambia automáticamente la velocidad de simulación;
se utiliza la velocidad seleccionada en los controles de AnyLogic.

Para el estudio comparativo, ejecutar `Comparacion_100x3` desde el árbol de
experimentos. Configura 100 iteraciones y tres réplicas por iteración: semilla
1 con escenarios 0, 1 y 2; luego semilla 2 con los mismos escenarios, hasta 100.
Cada corrida dura 100 semanas. La demanda se genera por clave para que no dependa
del orden de eventos; el estudio verifica su firma en cada terna.

Al terminar se publican `resultados.csv`, `series_semanales.csv`,
`ic_pareados.csv` y `metadata.txt` en una subcarpeta de `resultados_domitec`.
Si se inicia desde Estadísticas, se utiliza la carpeta elegida en Lógica.
El estudio aplica las políticas de los tres escenarios a una copia de la
configuración común de demanda y planta.

Los IC son pareados al 95%, con 100 diferencias por pareja. Pueden incluir cero.
El calentamiento inicial de 15 semanas es provisional: su adecuación y la
estacionariedad deben revisarse con las series reales del estudio. El diagnóstico
descriptivo se ejecuta con:

```powershell
python tools/diagnosticar_estacionariedad.py --help
```

Las pruebas de helpers y la compilación no sustituyen la corrida completa de
300 simulaciones. El estado de comprobación está en `verificacion_interfaz.json`
y los criterios pendientes en `../tools/revision_criterios.md`.

Si AnyLogic tenía abierto el modelo durante una corrección externa, cerrar la
simulación y el modelo **sin guardar la copia anterior**, volver a abrir este
archivo y ejecutarlo para regenerar su Java.
