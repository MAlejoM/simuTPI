# Domitec interactivo

Abrir `Domitec_Interactivo.alp` en AnyLogic 8.9.10 PLE. Para recorrer la interfaz,
ejecutar `Simulation_Escenario0_AsIs`: las pestañas son Vista 2D, Vista 3D,
Estadísticas y Lógica. Los parámetros se editan en Lógica y se confirman con
los botones de aplicar. Los lotes que ya están procesándose conservan su tiempo.

La vista 2D es un plano industrial esquemático de Parque y Vicentin, con
recepción, proceso, tanques, envasado y depósitos; muestra lotes, stock y backlog.
La pestaña 3D muestra la geometría de la planta. Los elementos
de programación están fuera del panel en el editor y ocultos en la ejecución.
La primera entrega ya no cambia automáticamente la velocidad de simulación;
se utiliza la velocidad seleccionada en los controles de AnyLogic.
La cámara inicial usa una **perspectiva centrada desde el costado**, igual que
**Restablecer cámara**. La vista superior sigue disponible en su botón.
El acercamiento a cada sector conserva su orientación desde arriba.
El piso y la señalización se incluyen
en la presentación 3D de Main.
Los operarios permanecen casi todo el tiempo en su puesto y realizan recorridos
ilustrativos cortos y esporádicos; esa animación no modifica la producción.

La pestaña 3D tiene una guía lateral de nueve sectores. Los números del piso
coinciden con sus botones; al seleccionar uno se explica qué se procesa o
almacena, y **Acercar al sector** lleva la cámara allí. **Restablecer cámara**
vuelve a la vista general.

En `DomitecPlant`, la vista de origen muestra el mismo plano 2D; en el editor
está a la izquierda, la geometría 3D al centro y la lógica a la derecha.
Los carteles 3D son grandes y se ubican dentro del sector correspondiente.
El dibujo 2D anterior se conserva
en un grupo oculto de compatibilidad para no romper referencias de código; sus
placas ya no se superponen con las máquinas 3D de la fase 4.

Para comparar los escenarios predeterminados, abrir directamente
**Comparacion_100x3** desde el árbol o el menú Run de AnyLogic y pulsar
**Ejecutar predeterminados**. No es necesario preparar una simulación normal.

Si se quieren usar parámetros personalizados:

1. En Estadísticas, pulsar **Guardar parámetros para estudio**. Guarda los parámetros comunes
   y la carpeta de salida en `domitec_estudio.properties`.
2. Cerrar esa ejecución y lanzar **Comparacion_100x3** desde el árbol de
   experimentos o el menú Run de AnyLogic. Elegir **Usar guardados y ejecutar**.
3. Al finalizar, volver a Main > Estadísticas > **Leer últimos IC** para cargar
   los resultados completos. El control Stop de la ventana del experimento
   permite interrumpirlo; un lote incompleto no se publica como resultado final.

El experimento configura 100 iteraciones y tres réplicas por iteración: semilla
1 con escenarios 0, 1 y 2; luego semilla 2 con los mismos escenarios, hasta 100.
Cada corrida dura 100 semanas. La demanda se genera por clave para que no dependa
del orden de eventos; el estudio verifica su firma en cada terna.

Al terminar se publican `resultados.csv`, `series_semanales.csv`,
`ic_pareados.csv` y `metadata.txt` en una subcarpeta de `resultados_domitec`,
con un marcador `COMPLETO` escrito al final. La publicación no renombra el
directorio ni elimina archivos si falla. **Reintentar guardado** vuelve a
exportar los 300 resultados retenidos, sin simularlos otra vez; mantener la
ventana abierta hasta que termine el guardado.
Con parámetros personalizados se utiliza la carpeta elegida en Lógica.
El estudio aplica las políticas de los tres escenarios a una copia de la
configuración común de demanda y planta.

El gráfico WIP violeta usa una escala independiente del backlog y se muestrea
cada hora simulada, para mostrar lotes que entran y salen entre dos controles
semanales. Este muestreo visual se cancela en el experimento de comparación;
las estadísticas del estudio conservan sus 100 observaciones semanales.

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
El lote real publicado fue revisado en `../tools/auditoria_estudio_real.md`:
300 resultados, 30.000 muestras semanales, demanda común por terna y 15 IC.
Los escenarios 1 y 2 coinciden en sus cinco indicadores; ese hallazgo requiere
revisar la lógica o sus supuestos antes de atribuir una mejora al escenario 2.

Si AnyLogic tenía abierto el modelo durante una corrección externa, cerrar la
simulación y el modelo **sin guardar la copia anterior**, volver a abrir este
archivo y ejecutarlo para regenerar su Java.
