# Domitec interactivo

La versión actual usa **24×7 (168 horas semanales)**, ritmos efectivos históricos,
cancelaciones con plazo editable y liberación limitada de lotes. La espera inicial
de 30 días y el límite de 36 lotes son **supuestos provisionales**, visibles en Configuración.
Los indicadores muestran insumos, cajas en proceso y cancelaciones por separado. Las salidas nuevas van a
`resultados_operativos_v2`; el 100×3 anterior no valida esta versión.
Ver [solución operativa y criterios de validación](../docs/solucion_operativa_24x7.md).
El estudio operativo 100×3 ya fue auditado; ver
[resultados 24×7](../docs/auditoria_resultados_24x7.md). La simplificación visual
posterior pasó las comprobaciones de compilación y cambio de pestañas; falta
confirmar su apariencia dentro de AnyLogic después de recargar el archivo.

Abrir `Domitec_Interactivo.alp` en AnyLogic 8.9.10 PLE. Para recorrer la interfaz,
ejecutar `Simulation_Escenario0_AsIs`. La interfaz conserva cuatro pestañas:

- **Planta 3D:** animación a todo el ancho, con datos, controles de cámara
  y referencias de los nueve números concentrados arriba.
- **Proceso 2D:** etapas, recorrido y cantidad de lotes en cada sector.
- **Estadísticas:** Gráficos, Indicadores y Comparar escenarios, por separado.
- **Configuración:** Escenarios, Demanda y Planta, con botones para aplicar cambios.

Los indicadores explican su significado junto al valor. Los cuatro gráficos
nombran el eje horizontal **Tiempo (semanas)** y el vertical con su cantidad
y unidad: cajas por semana, cajas pendientes o cajas en proceso. La demanda
mantiene el mismo color en los dos gráficos donde aparece.
Los lotes que ya están procesándose conservan su tiempo.

Cada nivel ocupa su propia fila: navegación principal, semana y escenario,
título, subpestañas y contenido. El estado de la corrida no envuelve las otras
vistas. Las referencias 3D se ordenan en tres filas: 1–4–5–8, 2–6–9 y 3–7,
manteniendo sus cuatro columnas alineadas y separando Parque de Vicentin.
En Comparar escenarios, una tabla muestra tres pares con diferencia media,
intervalo del 95% y una lectura breve. La diferencia siempre es A menos B;
servicio se expresa en puntos porcentuales, pendientes en cajas y efecto látigo
como diferencia de razones. Un intervalo que incluye cero no prueba igualdad.

En el editor de `Main`, cada vista tiene su propio panel a la derecha o debajo
del anterior. Esto evita que las pestañas se superpongan al abrir el diseño.
Al ejecutar, los paneles se recolocan en el mismo espacio y solo se muestra
la pestaña seleccionada.

La vista 2D muestra el flujo de lavandina con sus contadores y una tabla por
producto para los cinco líquidos: pulmón, envasado, stock y pedidos pendientes.
No incluye dibujos de pallets ni equipos; los textos y controles de Main
usan fuentes más grandes para facilitar la lectura.
La pestaña 3D muestra la geometría de la planta. Los elementos
de programación están fuera del panel en el editor y ocultos en la ejecución.
La primera entrega ya no cambia automáticamente la velocidad de simulación;
se utiliza la velocidad seleccionada en los controles de AnyLogic.
La cámara inicial usa una **perspectiva centrada desde el costado, más cercana**, igual que
**Perspectiva general**. La vista superior sigue disponible en su botón.
El acercamiento a cada sector conserva su orientación desde arriba.
El piso y la señalización se incluyen
en la presentación 3D de Main.
Los operarios permanecen casi todo el tiempo en su puesto y realizan recorridos
ilustrativos cortos y esporádicos; esa animación no modifica la producción.

Los números del piso identifican los sectores. La vista Proceso 2D permite
leer qué se elabora o almacena y qué significa el tanque pulmón.
La referencia de los números está arriba de la animación 3D. El escenario
**Mejora integral** explica en su descripción que supone un 27,5% más de cajas
por hora, manteniendo la apertura 24×7; el porcentaje no forma parte del nombre.

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

1. En Estadísticas > Comparar escenarios, pulsar **Guardar ajustes para el estudio**. Guarda los parámetros comunes
   y la carpeta de salida en `domitec_estudio.properties`.
2. Cerrar esa ejecución y lanzar **Comparacion_100x3** desde el árbol de
   experimentos o el menú Run de AnyLogic. Elegir **Usar guardados y ejecutar**.
3. Al finalizar, volver a Main > Estadísticas > Comparar escenarios > **Cargar resultados** para cargar
   los resultados completos. El control Stop de la ventana del experimento
   permite interrumpirlo; un lote incompleto no se publica como resultado final.

El experimento configura 100 iteraciones y tres réplicas por iteración: semilla
1 con escenarios 0, 1 y 2; luego semilla 2 con los mismos escenarios, hasta 100.
Cada corrida dura 100 semanas. La demanda se genera por clave para que no dependa
del orden de eventos; el estudio verifica su firma en cada terna.

Al terminar se publican `resultados.csv`, `series_semanales.csv`,
`ic_pareados.csv` y `metadata.txt` en una subcarpeta de `resultados_operativos_v2`,
con un marcador `COMPLETO` escrito al final. La publicación no renombra el
directorio ni elimina archivos si falla. **Reintentar guardado** vuelve a
exportar los 300 resultados retenidos, sin simularlos otra vez; mantener la
ventana abierta hasta que termine el guardado.
Con parámetros personalizados se utiliza la carpeta elegida en Comparar escenarios.
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

La simplificación visual conserva los experimentos, la demanda y la lógica
operativa. La auditoría del estudio 24×7 verifica 300 resultados, 30.000 muestras
semanales, demanda común por terna y 15 intervalos pareados. Ese estudio valida
los archivos de resultados; la revisión de la nueva interfaz dentro de AnyLogic
sigue siendo una comprobación distinta.

Si AnyLogic tenía abierto el modelo durante una corrección externa, cerrar la
simulación y el modelo **sin guardar la copia anterior**, volver a abrir este
archivo y ejecutarlo para regenerar su Java.
