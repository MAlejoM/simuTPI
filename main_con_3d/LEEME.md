Abrir **Domitec_Main_3D.alp** en AnyLogic y ejecutar **Simulation_Escenario0_AsIs**.
Desde el panel principal, pulsar **Ver planta 3D**. Dentro de la planta,
**Volver a resultados** regresa al panel. **Recorridos de operarios** activa o
desactiva el movimiento de las personas.

La base funcional se extrajo de la rama local **main**, commit
**eceeeb5a29778c183460a2d52327cba57383a27e**. Se conserva su selector interactivo de
escenarios, sus tarjetas de resultados, parámetros, demanda, planificación,
entregas, capacidades, conexiones, clases y sus seis experimentos originales. Se incluyen los cambios del último pull:
100 réplicas y el generador aleatorio basado en getCurrentReplication() para
comparar los escenarios con semillas comunes.
Los cuerpos Java de los eventos están integrados dentro del archivo `.alp`.

Se incorporó la presentación de Domitec_3D_Interior: equipos, camiones,
autoelevadores, depósitos, seis controles de peso, selladora térmica ilustrativa,
productos animados, señalización y operarios con pausas y recorridos.
Se retiraron 126 figuras de plantilla o instancias antiguas ocultas. Solo se
copiaron las 27 mallas utilizadas y las texturas que requieren. No hay edificio
exterior ni controles de fábrica.

Los callbacks añadidos registran los lotes para dibujarlos: no alteran stock,
producción, rechazos ni demoras. La primera recepción de lavandina ajusta la
velocidad de reproducción a 15 minutos simulados por segundo, como en la versión
visual anterior. La velocidad se puede cambiar desde los controles de AnyLogic.

Se verificó el archivo entregado contra main y se compilaron las acciones de
arranque, los eventos activos, los 23 callbacks, la recepción y la navegación
contra la API y las clases generadas por AnyLogic 8.9.10. Se comprobaron las
referencias de recursos, la limpieza y las alturas de los productos y cintas.
Esta comprobación no incluye una nueva corrida nativa completa de 100 semanas.

La carpeta contiene su propia base de datos, tomada del mismo commit de main,
y recursos. Se puede abrir junto a los proyectos anteriores. No se cambió la
rama activa, no se hizo un merge Git ni se sobrescribieron archivos originales.
El detalle auditable está en **integracion_main.json**. Los scripts de integración
y verificación están en **tools/integrar_main_3d.py** y
**tools/verificar_integracion_main.py**.

Para compartir el modelo hay que incluir esta carpeta completa: el `.alp`,
las mallas de `3d/` y el conjunto de archivos de `database/`. No basta con copiar
únicamente el archivo `.alp`. La base conserva el snapshot de main; `db.log`
forma parte de ese snapshot porque fue guardado con modified=yes.
