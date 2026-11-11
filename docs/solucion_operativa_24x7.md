# Corrección del modelo operativo de Domitec

La planta abre **24 horas, los siete días: 168 horas semanales**, según la última
aclaración del grupo. La apertura no equivale a 168 horas de producción a velocidad
nominal en todas las líneas. Esta versión separa calendario, rendimiento observado,
materiales en almacén, trabajo liberado y servicio a clientes.

## Qué estaba mal

1. **Demanda pendiente sin vencimiento.** Un pedido no atendido quedaba en una deuda
   escalar hasta ser entregado, aunque el cliente real pudiera cancelarlo. Esa deuda
   también aumentaba las compras por el factor látigo.
2. **Liberación inmediata de toda una entrega.** Cada camión inyectaba sus lotes de
   1.000 cajas a las colas. El indicador sumaba todo ese material como proceso, aunque
   una parte representara insumos esperando en recepción. Algunas colas y tanques
   tenían `maximumCapacity=true`: su capacidad numérica no actuaba como límite.
3. **Calendario supuesto de 40 horas.** Los tiempos se multiplicaban por `168/40`.
   Cambiar solamente ese factor a 1 aceleraría la planta 4,2 veces sin contrastar
   la producción histórica.
4. **Demanda normal recortada en cero.** Cuando la dispersión es grande, recortar
   los valores negativos aumenta la media resultante. Los parámetros nominales de
   una normal dejan de ser la media y el desvío de los pedidos generados.

El antiguo evento `avanceProduccion`, con un segundo esquema de seis máquinas,
estaba excluido de compilación. No se atribuye a ese código una doble producción
en las corridas anteriores. Ahora ese evento se reutiliza exclusivamente para
cancelaciones y liberación: el flujo productivo que acredita stock sigue siendo PML.

## Lo que dicen los datos

Las planillas originales se conservaron. Se excluye la fila `Total` de demanda,
y `prod.csv` y `prod1.csv` no se suman porque son versiones superpuestas.

En **2025**, para todos los rubros de la planilla:

| Pedidas | Despachadas | Canceladas | Pendientes registradas |
|---:|---:|---:|---:|
| 3.242.281 | 2.977.002 | 265.279 | 0 |

La identidad `pedidas = despachadas + canceladas + pendientes` se cumple en todas
las filas. Las cancelaciones representan aproximadamente **8,18%** de los pedidos
de ese año. Es un resultado histórico para contrastar, **no una probabilidad que se
impone al simulador**. En 2026 sí hay pendientes registrados (246.034 en el corte
del archivo); por tanto, tampoco corresponde cancelar toda falta automáticamente.

Los estados finales de las filas no identifican cuándo se canceló cada pedido ni
su tiempo de espera. Cero pendientes en pedidos antiguos puede deberse al cierre
posterior de esas cohortes; no prueba que se cancelen el mismo día.

Se remuestrean los doce meses de pedidos de **2025** para las seis familias
representadas y los tres canales. Lavandina común y concentrada se agrupan.
Promopack, limpiador y bactericida quedan fuera de esas seis familias: sus totales
no se deben comparar directamente con la salida agregada del modelo reducido.
Para las **seis familias incluidas**, 2025 registra 2.980.891 pedidas,
2.731.857 despachadas y 249.034 canceladas (**8,35%**), sin pendientes en ese corte.
Ese es el agregado de demanda comparable por alcance, aunque el año de producción
sigue sin estar identificado.

El mes se convierte a cajas por semana usando sus días reales. Un mismo mes
remuestreado se comparte entre productos y canales en bloques de cuatro semanas,
conservando su relación y la demanda común entre los tres escenarios de una semilla.
Es una aproximación de escala mensual: **no permite estimar picos o variación diaria**.
Los controles de media/desvío reescalan ese perfil; si el usuario elige valores que
generan cantidades negativas se recortan en cero y ya no se garantiza la media elegida.

## Ritmo de producción usado

Para no multiplicar la producción por el cambio de turno, se utiliza como referencia
el promedio observado de cajas terminadas de enero a agosto de `prod.csv` por hora
de apertura. Se excluye septiembre, que parece parcial. Ese archivo **no tiene año**;
la comparación con demanda es orientativa y no una validación de períodos coincidentes.

Denominador de referencia: `8 × (365/12) × 24 = 5.840 horas abiertas`.
Usar el mes medio evita inventar el año de producción.

| Familia | Cajas enero–agosto | Cajas/h de apertura | Referencia cajas/semana a 168 h |
|---|---:|---:|---:|
| Lavandina común + concentrada | 943.087 | 161,49 | 27.130 |
| Desinfectante | 426.507 | 73,03 | 12.269 |
| Lavavajilla | 470.742 | 80,61 | 13.542 |
| Lavarropa | 231.640 | 39,66 | 6.664 |
| Suavizante | 132.007 | 22,60 | 3.797 |
| Detergente concentrado | 86.900 | 14,88 | 2.500 |

Son **ritmos efectivos históricos**, que incorporan la asignación observada de
producción, paradas y cambios. No son capacidades mecánicas máximas ni permiten
separar esas causas. No se debe aplicar otra vez la disponibilidad/OEE del archivo
a estos ritmos, porque se contaría dos veces su efecto.
Por el mismo motivo, el rechazo **adicional** de QC queda inicialmente en **0%**:
se mantiene el recorrido de calidad, pero no se descuentan otra vez los antiguos
3%/5% sobre un ritmo de cajas terminadas. Los controles de rechazo permiten estudiar
pérdidas adicionales como hipótesis; para modelar merma medida por separado habría
que recalibrar el ritmo bruto y confirmar qué representa `Cajas` en producción.

También se conservan las tasas por hora registrada en `Tiempo` como contraste,
interpretándolo provisionalmente en minutos. La similitud de
`Cajas/(Tiempo/60)/Operarios` con `Prod/Hs/Ho` respalda esa interpretación.
`prod3.csv` indica 330 horas mensuales en varias líneas y datos de equipos de trabajo;
eso no es equivalente al calendario de apertura de la fábrica.

## Pedidos que vencen

Cada parte pendiente conserva producto, fecha de entrada y cantidad. Se atiende FIFO.
Al vencer el plazo, se registra como cancelada y deja de integrar el backlog y la
necesidad de reposición. Una cancelación **no cuenta como entrega** y sigue incluida
en la demanda usada como denominador del nivel de servicio.

El panel Lógica incorpora **“Cancelación: espera SUPUESTA (días)”**. El valor inicial
de **30 días** es una hipótesis basada en la granularidad mensual de los datos,
no una estimación de paciencia del cliente. Deben compararse al menos:

| Espera | Interpretación |
|---:|---|
| 0 días | Venta perdida inmediata si falta stock |
| 7 días | El cliente tolera una semana |
| 30 días | El cliente tolera aproximadamente un mes |

Elegir posteriormente un plazo compatible con la proporción cancelada, los pendientes
y el nivel de servicio de una ventana comparable. Es posible que varias políticas
produzcan los mismos totales mensuales: no corresponde afirmar que se identificó
un plazo único con esta planilla.

## Liberación de producción y WIP

El recorrido es: **pedido al proveedor → insumos en tránsito → insumos almacenados →
lote liberado → elaboración/QC/envasado → terminado o rechazo**.

Una recepción agrega material a `BalanceMateriales.materiaPrima`; no crea de inmediato
cientos de lotes. Cada lote requiere una tarjeta de liberación. Al terminar o ser
rechazado devuelve su tarjeta. Las colas, tanques y máquinas tienen capacidades
explícitas y finitas, y el contador incluye también los lotes retenidos en Sources.

El panel incorpora **“Límite PROVISIONAL de lotes liberados”**, inicialmente **36**.
Además existe un límite por producto de `capacidadTanque + 3` lotes (6 por defecto).
Es una política de control a evaluar; el plano y las planillas no acreditan que 36
sea la capacidad física real de almacenamiento.

Ese límite **controla la entrada**, no recorta el gráfico ni borra material. Por
ejemplo, recibir 800.000 cajas equivalentes de un solo producto y permitir seis
lotes deja 6.000 en proceso y 794.000 en insumos. La sobrecompra sigue visible. La
reposición incluye insumos almacenados, tránsito y WIP para no comprar otra vez lo
que ya está disponible. El stock objetivo se calcula con demanda media y cobertura,
en lugar de confundir cobertura de demanda con capacidad nominal de máquina.

El pie del panel informa canceladas, insumos almacenados y WIP por separado.
El cierre comprueba las identidades:

```text
Demanda = entregada + cancelada + pendiente
Material recibido = insumos almacenados + WIP + terminado + rechazo
```

Los inventarios iniciales de producto terminado se conservan como condición de
arranque del modelo anterior; aún necesitan validarse contra inventarios reales.
No se supone que los datos disponibles identifiquen el stock inicial ni las
capacidades de cada tanque. Los tiempos de preparación anteriores se conservan
como hipótesis pendientes de contraste.

## Escenarios y resultados anteriores

- **0: Base 24×7.** Reposición reactiva, factor 1,5.
- **1: Sin pánico 24×7.** Factor 1,0, mismo calendario y ritmo base.
- **2: Rendimiento +27,5%.** Factor 1,0 y mejora hipotética del ritmo de envasado.
  Se conserva la mejora relativa del diseño anterior `51/40`, pero ya no se
  presentan horas extra ficticias en una fábrica que abre 168 horas semanales.
  La mejora no está probada en la planta y no representa un resultado observado.

Se mantienen 100 semanas, 100 semillas y tres escenarios por semilla. Las nuevas
salidas se guardan en **`resultados_operativos_v2`**. El CSV final agrega canceladas
de pedidos ingresados tras el calentamiento, máximo WIP de toda la corrida e insumos al cierre.
Las cancelaciones mostradas en vivo incluyen toda la corrida.

El paquete anterior 100×3 se conserva sin modificar. Sus resultados y los textos
anteriores de `main.tex`/`exposicion.tex` **no validan esta nueva versión**. Antes de
actualizar conclusiones se debe ejecutar el modelo nuevo y repetir el estudio.

## Comprobaciones y uso

1. Recargar `domitec_interactivo/Domitec_Interactivo.alp` y ejecutar
   `Simulation_Escenario0_AsIs`.
2. En Lógica revisar 168 horas, espera supuesta, límite de liberación y ritmo de
   cada producto. Si se cambian parámetros, aplicarlos con el botón correspondiente.
3. Observar WIP, insumos, canceladas, producción semanal y pendientes por producto;
   no evaluar solo el total de planta.
4. Contrastar primero una corrida completa y después repetir el 100×3. Para comparar
   plazos, guardar cada configuración explícitamente y conservar sus metadatos.

Pasaron las pruebas del reloj, FIFO y cancelaciones, conservación de materiales,
remuestreo, persistencia y exportación. Las acciones y propiedades serializadas
compilan contra la API de AnyLogic; las vistas conservan sus comprobaciones de cámara.
**La nueva corrida nativa y su calibración estadística quedan pendientes**: las pruebas
de componentes y la compilación no equivalen a haber ejecutado el nuevo 100×3.

Fuentes locales: `demanda/demanda - Sheet1.csv`, `produccion/prod.csv`,
`produccion/prod1.csv`, `produccion/prod3.csv`. Sus hashes y los desgloses están en
`diagnostico_datos_operativos.json` y su resumen Markdown.
La semántica de capacidades se contrastó con la documentación oficial de
[Queue](https://www.anylogic.help/online/libraries/process-modeling/queue.html) y
[Delay](https://www.anylogic.help/online/libraries/process-modeling/delay.html).
