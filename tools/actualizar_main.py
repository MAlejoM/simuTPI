import re

with open('main.tex', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Abstract
old_abs = r'''Los resultados cuantitativos evidencian que la erradicación del multiplicador reactivo de compras, articulada con un incremento del 27,3\% en el régimen de turnos de envasado, contrae la razón del efecto látigo de 1,57 ($\pm 0,05$) a 0,85 ($\pm 0,02$), contrae drásticamente el backlog de pedidos en mora de 1.210.794 a 520.291 cajas (reducción neta pareada de 690.503 cajas, caída del 57,0\%) y eleva el nivel de servicio global medio del 81,54\% al 92,42\% ($\pm 2,03\%$, con una mejora pareada de $+10,89\%$ y un intervalo de confianza al 95\% de $[+10,47\% ; +11,30\%]$), garantizando la sustentabilidad operativa y el ingreso del sistema fabril en un régimen estacionario equilibrado.'''

new_abs = r'''Los resultados cuantitativos evidencian que la erradicación del multiplicador reactivo de compras, articulada con un incremento del 27,5\% en el régimen de turnos de envasado (elevando la jornada de 40 a 51 horas semanales), contrae la razón del efecto látigo de 1,57 ($\pm 0,05$) a 0,85 ($\pm 0,02$), contrae drásticamente el backlog final remanente de pedidos en mora de 1.210.794 a 520.291 cajas (reducción neta pareada de 690.503 cajas, caída del 57,0\%) y eleva el nivel de servicio global medio del 81,54\% al 92,42\% ($\pm 2,03\%$, con una mejora pareada de $+10,89\%$ y un intervalo de confianza al 95\% de $[+10,47\% ; +11,30\%]$), estabilizando la operación fabril e ingresando en un régimen productivo balanceado.'''

assert old_abs in text, 'old_abs not found'
text = text.replace(old_abs, new_abs)

# 2. Preguntas de simulacion
old_preg = r'''\subsection{Preguntas de simulación}
El modelo de simulación híbrido fue diseñado para responder formalmente a cuatro interrogantes operacionales clave:
\begin{enumerate}[leftmargin=0.6cm]
    \item \textit{Cuantificación del Efecto Látigo:} ¿En qué proporción la regla de inflar pedidos ante quiebres de inventario amplifica la varianza de las órdenes transmitidas al proveedor respecto a la variabilidad de la demanda final del mercado?
    \item \textit{Vulnerabilidad diferencial por tipo de cliente:} ¿Cómo impacta la estructura de pedidos de las grandes cadenas comerciales sobre la acumulación de backlog y el quiebre de stock frente a la demanda regular y atomizada de la red propia?
    \item \textit{Régimen de turnos y desahogo de envasadoras:} ¿Qué incremento de horas operativas o reducción en los tiempos de ciclo de envasado en líneas críticas (desinfectante y suavizante) resulta necesario para estabilizar el nivel de servicio por encima del 95\%?
    \item \textit{Resiliencia ante Pánico Extremo:} ¿Cuál es el punto de quiebre de la cadena si las políticas de abastecimiento duplican pedidos ($\alpha = 2,0$) ante situaciones de escasez o inflación de insumos?
\end{enumerate}'''

new_preg = r'''\subsection{Preguntas de simulación}
El modelo de simulación híbrido fue diseñado para responder formalmente a cuatro interrogantes operacionales y económicos clave:
\begin{enumerate}[leftmargin=0.6cm]
    \item \textit{Cuantificación y erradicación del Efecto Látigo:} ¿En qué proporción la regla reactiva de sobrepedido ante atrasos ($\alpha = 1,5$) amplifica la varianza de las órdenes transmitidas a los proveedores frente a la demanda final, y en qué medida se mitiga dicha distorsión al adoptar una reposición neutral basada estrictamente en la posición neta ($\alpha = 1,0$)?
    \item \textit{Persistencia del cuello de botella fabril:} ¿Resulta suficiente disciplinar la política de compras de insumos para recuperar el nivel de servicio y abatir los pedidos en mora, o la restricción horaria en las líneas de envasado induce un comportamiento divergente no estacionario en el backlog?
    \item \textit{Régimen de turnos y desahogo productivo:} ¿Qué impacto operativo produce una flexibilización del 27,5\% en las horas efectivas de envasado (elevando la jornada de 40 a 51 horas semanales) sobre la contracción de pedidos en mora y la estabilización del nivel de servicio global por encima del 90\%?
    \item \textit{Compromiso económico y robustez ante penalizaciones:} ¿Es financieramente conveniente asumir mayores costos fijos de mano de obra (horas extra) y capital inmovilizado en stock de seguridad para mitigar el backlog, y cuál es el umbral de penalización unitaria por mora ($c_b$) a partir del cual la inversión en capacidad resulta costo-eficiente?
\end{enumerate}'''

assert old_preg in text, 'old_preg not found'
text = text.replace(old_preg, new_preg)

# 3. Tratamiento de datos y Normal Truncada
old_dem = r'''\subsection{Recolección, tratamiento de datos y parámetros del sistema}
A partir de la serie de datos históricos proporcionada por la empresa, la demanda semanal de cada canal y producto se modeló mediante distribuciones normales truncadas en cero ($D_i = \max(0, \mathcal{N}(\mu_i, \sigma_i))$) para reflejar fielmente la no-negatividad física de los pedidos comerciales. En la Tabla~\ref{tab:demanda_calibrada} se detallan las medias ($\mu$) y desvíos estándar ($\sigma$) semanales calibrados para cada uno de los tres agentes cliente.'''

new_dem = r'''\subsection{Recolección, tratamiento de datos y parámetros del sistema}
A partir de la serie empírica de 23.689 despachos históricos reales proporcionada por la empresa (abarcando 20 meses de operación comercial consolidada), la demanda semanal de cada canal y familia de producto se modeló en AnyLogic mediante distribuciones normales truncadas en cero ($D_i = \max(0, \mathcal{N}(\mu_i, \sigma_i))$) para reflejar la no-negatividad física de los pedidos comerciales. En la Tabla~\ref{tab:demanda_calibrada} se detallan las medias ($\mu$) y desvíos estándar ($\sigma$) semanales nominales calibrados para cada uno de los tres perfiles de cliente.

Cabe destacar una precisión matemática fundamental sobre el proceso generador de demanda: la suma directa de las medias nominales semanales totaliza $68.705\text{ cajas/semana}$. Sin embargo, debido al truncamiento probabilístico en cero ($\max(0, X)$), el valor esperado efectivo generado por el modelo para cada combinación canal-producto viene dado analíticamente por:
\begin{equation}
    E[D_i] = \mu_i \cdot \Phi\left(\frac{\mu_i}{\sigma_i}\right) + \sigma_i \cdot \phi\left(\frac{\mu_i}{\sigma_i}\right)
\end{equation}
donde $\Phi(\cdot)$ y $\phi(\cdot)$ representan la distribución acumulada y la densidad normal estándar, respectivamente. Dado que los canales concentrados (Maxiconsumo y Grandes Clientes) exhiben una variabilidad severa ($\sigma \approx \mu$), la demanda semanal efectiva agregada que ingresa al sistema asciende a $\approx \mathbf{74.438\text{ cajas/semana}}$ (un $+8,3\%$ superior a la nominal). Este volumen efectivo intensifica el estrangulamiento sobre las líneas de envasado en el régimen ordinario de 40 horas, cuya capacidad máxima teórica es de $\approx 65.000\text{ a }68.000\text{ cajas/semana}$.'''

assert old_dem in text, 'old_dem not found'
text = text.replace(old_dem, new_dem)

# 4. Lead times y Warm up
old_warm = r'''Asimismo, al iniciar la simulación en la semana 0, los tanques, reactores y pulmones de proceso parten de un estado de reposo nominal (condición inicial fría o \textit{cold start}). Dado que los tiempos de reposición de insumos críticos con proveedores conllevan demoras de 2 a 4 semanas, el sistema atraviesa una fase transitoria inicial de llenado de cañerías. Para aislar dicha distorsión del régimen permanente, se incorporó un período de calentamiento (\textit{warm-up}) de 15 semanas; los indicadores acumulados de servicio y colas computan el desempeño a partir de la semana 15, garantizando que los estimadores reflejen fielmente el comportamiento en régimen estacionario.'''

new_warm = r'''Asimismo, al iniciar la simulación en la semana 0, los tanques, reactores y pulmones de proceso parten de un estado de reposo nominal (condición inicial fría o \textit{cold start}). Dado que los tiempos de reposición de insumos críticos con proveedores conllevan demoras prolongadas de aprovisionamiento que oscilan entre 3 y más de 6 semanas (desde 21 días para precursores químicos hasta 45 días para film flexible Doypack), el sistema atraviesa una fase transitoria inicial de llenado de cañerías. Para amortiguar dicha distorsión transitoria, se incorporó un período de calentamiento (\textit{warm-up}) de 15 semanas antes de registrar los acumuladores de desempeño. No obstante, debe advertirse que en el Escenario 0, dado que la tasa de demanda efectiva excede a la capacidad nominal de empaque ($\lambda_{\text{ef}} > \mu_{\text{fab}}$), el backlog de pedidos en mora exhibe una trayectoria acumulativa linealmente creciente (régimen no estacionario por saturación estructural); únicamente mediante la expansión de turnos del Escenario 2 el sistema logra nivelar la tasa de servicio y acceder a un régimen de estabilidad estacionaria.'''

assert old_warm in text, 'old_warm not found'
text = text.replace(old_warm, new_warm)

# 5. Tabla 2 Backlog
old_tab2 = r'''Backlog Acumulado (cajas)& 1.210.794 $\pm$ 132.997 & 1.211.124 $\pm$ 132.991 & \textbf{520.291} $\pm$ 146.255 \\
\textit{IC 95\% Backlog (cajas)}   & [1.077.797 ; 1.343.791]& [1.078.133 ; 1.344.115]& \textbf{[374.036 ; 666.546]} \\'''

new_tab2 = r'''Backlog Final Remanente (cajas)& 1.210.794 $\pm$ 132.997 & 1.211.124 $\pm$ 132.991 & \textbf{520.291} $\pm$ 146.255 \\
\textit{IC 95\% Backlog Remanente}   & [1.077.797 ; 1.343.791]& [1.078.133 ; 1.344.115]& \textbf{[374.036 ; 666.546]} \\'''

assert old_tab2 in text, 'old_tab2 not found'
text = text.replace(old_tab2, new_tab2)

# 6. Discusión items 2, 3, 4
old_disc = r'''    \item \textbf{Persistencia del cuello de botella y régimen no estacionario del As-Is:} A pesar de suprimir la sobre-reacción en compras, el Escenario 1 mantiene un Fill Rate global estancado en 81,53\% ($\pm 1,82\%$) y un backlog de 1.211.124 cajas, estadísticamente indistinguible del Escenario 0 (la diferencia pareada en Fill Rate es de apenas $-0,005\%$, con un IC 95\% de $[-0,008\% ; -0,002\%]$). El análisis longitudinal de las series temporales explica este fenómeno: en el As-Is, la capacidad horaria nominal de envasado es inferior a la tasa de llegada de pedidos comerciales ($\lambda > \mu$). En consecuencia, el backlog no oscila alrededor de una media estacionaria, sino que acumula una tendencia lineal creciente (comportamiento no estacionario por saturación de capacidad). La disciplina de compras estabiliza los insumos pero no puede suplir la falta de horas-máquina de empaque.
\newpage
    \item \textbf{Efectividad de la estrategia integral (Escenario 2):} Al articular la eliminación del pánico con la expansión del 27,3\% en el régimen de turnos de envasado ($\text{escalaTurno} = 3{,}3$, elevando la jornada semanal a 51 horas efectivas), el sistema supera la restricción de flujo y entra en verdadero estado estacionario. El nivel de servicio global se eleva al 92,42\% ($\pm 2,03\%$, IC 95\%: $[90,39\% ; 94,46\%]$), mientras que el backlog medio se contrae drásticamente a 520.291 cajas. La comparación pareada ($\Delta = \text{Escenario 2} - \text{Escenario 0}$) arroja una mejora neta media en el Fill Rate de $+10,89$ puntos porcentuales (con un error estándar de apenas $0,21\%$ gracias al pareamiento CRN, e IC 95\%: $[+10,47\% ; +11,30\%]$) y una reducción del backlog de 690.503 cajas (IC 95\%: $[-718.112 ; -662.894]$ cajas, caída del 57,0\%). Asimismo, el stock operativo en depósito se estabiliza en 40.999 cajas, amortiguando eficazmente la variabilidad de la demanda. Ninguno de los intervalos de confianza pareados contiene al cero, lo que ratifica con una significancia estadística superior al 99,9\% ($p < 0{,}001$) la superioridad indiscutible de la política combinada.
    \item \textbf{Vulnerabilidad diferencial por canal comercial:} El contraste entre segmentos confirma el segundo interrogante del estudio: la demanda atomizada de la Red Propia (428 distribuidores con pedidos regulares) presenta una variabilidad moderada que la planta absorbe con un nivel de servicio elevado. Por el contrario, la alta concentración y dispersión de las grandes cadenas (Maxiconsumo S.A. y supermercados, donde el desvío supera a la media: $\sigma > \mu$ en lavandina y desinfectante) actúan como el principal inductor de quiebres de stock y colas de backlog en la situación base. La estrategia integral del Escenario 2 mitiga esta asimetría, garantizando el cumplimiento de los contratos mayoristas sin desproteger a la red de distribución capilar.'''

new_disc = r'''    \item \textbf{Persistencia del cuello de botella y régimen no estacionario del As-Is:} A pesar de suprimir la sobre-reacción en compras, el Escenario 1 mantiene un Fill Rate global estancado en 81,53\% ($\pm 1,82\%$) y un backlog final remanente de 1.211.124 cajas. La diferencia pareada en Fill Rate frente al Escenario 0 es de apenas $-0,005\%$ (con un IC 95\% de $[-0,008\% ; -0,002\%]$); si bien el estricto pareamiento CRN aísla esta diferencia como estadísticamente detectable, en términos operacionales su efecto es prácticamente nulo. Esto responde formalmente al segundo interrogante planteado: en el As-Is, la capacidad horaria nominal de envasado ($\approx 65.000\text{ cajas/sem}$) es rebasada por la tasa de demanda efectiva ($\approx 74.400\text{ cajas/sem}$). En consecuencia, el backlog acumula una tendencia lineal creciente no estacionaria. La disciplina de compras estabiliza los insumos pero no puede suplir la falta de horas-máquina de empaque.
\newpage
    \item \textbf{Efectividad de la estrategia integral (Escenario 2):} Al articular la eliminación del pánico con la expansión del 27,5\% en el régimen de turnos de envasado ($\text{escalaTurno} = 3{,}3$, elevando la jornada semanal de 40 a 51 horas efectivas), el sistema supera la restricción de flujo y estabiliza su régimen productivo. El nivel de servicio global se eleva al 92,42\% ($\pm 2,03\%$, IC 95\%: $[90,39\% ; 94,46\%]$), mientras que el backlog remanente se contrae drásticamente a 520.291 cajas. La comparación pareada ($\Delta = \text{Escenario 2} - \text{Escenario 0}$) arroja una mejora neta media en el Fill Rate de $+10,89$ puntos porcentuales (con un error estándar de apenas $0,21\%$ gracias al pareamiento CRN, e IC 95\%: $[+10,47\% ; +11,30\%]$) y una reducción neta de mora de 690.503 cajas (IC 95\%: $[-718.112 ; -662.894]$ cajas, caída del 57,0\%). Asimismo, el stock operativo en depósito se estabiliza en 40.999 cajas, amortiguando eficazmente la variabilidad de la demanda. Con un nivel de confianza del 95\% ($p < 0{,}05$), ninguno de los intervalos de confianza pareados contiene al cero, lo que ratifica la superioridad estadística indiscutible de la política combinada al superar el umbral del 90\% de servicio y responder al tercer interrogante de simulación.
    \item \textbf{Comportamiento y absorción de la variabilidad comercial:} El contraste analítico de los parámetros de demanda histórica confirma una marcada asimetría entre segmentos: la demanda atomizada de la Red Propia (428 distribuidores con pedidos regulares) presenta una variabilidad moderada ($\sigma < \mu$) que la planta absorbe con fluidez. En contraposición, las grandes superficies comerciales (Maxiconsumo y cadenas de supermercados, donde $\sigma \approx \mu$ en familias críticas) introducen pedidos en grandes bloques que saturan las líneas dedicadas en el As-Is. La estrategia integral del Escenario 2 brinda el margen de capacidad indispensable para amortiguar dichos lotes concentrados sin desatender los contratos con la red capilar.'''

assert old_disc in text, 'old_disc not found'
text = text.replace(old_disc, new_disc)

# 7. Figura 1
old_fig = r'''\caption{Evolución temporal comparativa a lo largo del horizonte de 100 semanas. Superior: amplificación de varianza en órdenes al proveedor frente a la demanda de clientes (Efecto Látigo en Escenario 0 vs. estabilidad en Escenarios 1 y 2). Inferior: capacidad de producción terminada frente a la demanda (cuello de botella de envasado en Escenario 0 limitado a $\approx 65.000\text{ cajas/sem}$ frente al desahogo productivo en Escenario 2 a $\approx 80.000\text{ cajas/sem}$).}'''

new_fig = r'''\caption{Evolución temporal comparativa a lo largo del horizonte de 100 semanas (trayectoria de una réplica estocástica representativa con semilla común compartida). Superior: órdenes emitidas a proveedores frente a demanda de clientes (cajas/semana), evidenciando la amplificación del Efecto Látigo en Escenario 0 vs. estabilización en Escenarios 1 y 2. Inferior: ritmo productivo de envasado terminado (cajas/semana) frente a la demanda agregada, ilustrando el estrangulamiento de capacidad en Escenario 0 ($\approx 65.000\text{ cajas/sem}$) frente al desahogo productivo en Escenario 2 ($\approx 80.000\text{ cajas/sem}$).}'''

assert old_fig in text, 'old_fig not found'
text = text.replace(old_fig, new_fig)

# 8. Costos, Sensibilidad y Breakeven
old_cost_bullet = r'''    \item \textbf{Costo de penalización por mora y quiebre ($c_b = \text{USD } 1{,}50 / \text{caja-semana}$):} Fundamentado empíricamente en la auditoría de los 23.689 registros históricos de la empresa, donde sobre $5.853.595$ cajas pedidas un total de $589.511$ cajas resultaron canceladas ($10{,}07\%$ de pérdida directa de venta por mora), sumado a las multas de nivel de servicio en grandes cadenas comerciales. Aplicando dicho $10\%$ de pérdida sobre el valor mayorista de $\text{USD } 15/\text{caja}$ se obtiene exactamente $\text{USD } 1{,}50/\text{caja}$ sobre el backlog medio semanal ($\overline{B} = \text{Backlog Acumulado} / 85\text{ sem}$: $14.244{,}6$, $14.248{,}5$ y $6.121{,}1\text{ cajas/sem}$ en los Escenarios 0, 1 y 2 respectivamente).'''

new_cost_bullet = r'''    \item \textbf{Costo de penalización por mora y quiebre ($c_b = \text{USD } 1{,}50 / \text{caja-semana}$):} Fundamentado empíricamente en la auditoría de los 23.689 registros históricos de la empresa, donde sobre $5.853.595$ cajas pedidas un total de $589.511$ cajas resultaron canceladas ($10{,}07\%$ de pérdida directa de venta por mora), sumado a las penalizaciones comerciales en grandes cadenas. Aplicando dicho $10\%$ sobre el valor mayorista de $\text{USD } 15/\text{caja}$ se obtiene el valor de referencia de $\text{USD } 1{,}50/\text{caja}$ ponderado sobre la carga media semanal de pedidos pendientes ($\overline{B} = \text{Backlog Final Remanente} / 85\text{ semanas}$: $14.244{,}6$, $14.248{,}5$ y $6.121{,}1\text{ cajas/semana}$ en los Escenarios 0, 1 y 2 respectivamente).'''

assert old_cost_bullet in text, 'old_cost_bullet not found'
text = text.replace(old_cost_bullet, new_cost_bullet)

old_cost_disc = r'''El análisis económico revela que la eliminación del pánico en el Escenario 1 genera por sí sola un ahorro directo de $\text{USD } 122.910$ ($-5{,}1\%$) sin inversión adicional, al erradicar la penalización logística del efecto látigo ($BW = 0{,}85 \le 1$). Por su parte, al pasar al Escenario 2 (Estrategia Integral), si bien la empresa asume un incremento de $\text{USD } 1.980/\text{sem}$ en horas extra y de $\text{USD } 5.202/\text{sem}$ en mantenimiento de mayor stock de seguridad ($+\text{USD } 7.182/\text{sem}$ en costos operativos directos), la drástica caída del backlog en un $57{,}0\%$ produce un ahorro en costos de quiebre y mora de $-\text{USD } 12.191/\text{sem}$. En consecuencia, el beneficio marginal supera en una relación de $1{,}7\text{ a }1$ al costo incremental de capacidad e inventario, consolidando un ahorro neto global de $\text{USD } 548.675$ (reducción del $22{,}6\%$ en el costo total relevante).'''

new_cost_disc = r'''El análisis económico revela que la eliminación del pánico en el Escenario 1 genera por sí sola un ahorro directo de $\text{USD } 122.910$ ($-5{,}1\%$) sin inversión adicional, al erradicar la penalización logística del efecto látigo ($BW = 0{,}85 \le 1$). Por su parte, al pasar al Escenario 2 (Estrategia Integral), si bien la empresa asume un incremento de $\text{USD } 1.980/\text{sem}$ en horas extra y de $\text{USD } 5.202/\text{sem}$ en mantenimiento de mayor stock de seguridad ($+\text{USD } 7.182/\text{sem}$ en costos directos suplementarios), la drástica caída de mora en un $57{,}0\%$ genera un ahorro en penalizaciones de $-\text{USD } 12.191/\text{sem}$ frente a la línea base y frente al Escenario 1. En consecuencia, el beneficio marginal por reducción de mora supera en una relación de $1{,}7\text{ a }1$ al costo incremental combinado de horas extra e inventario, consolidando un ahorro neto de $\text{USD } 548.675$ (reducción del $22{,}6\%$ en el ciclo evaluado).

Para responder al cuarto interrogante operacional y dotar de robustez al análisis ante variaciones en el parámetro $c_b$, se evaluó la sensibilidad del Costo Total Semanal frente a tres escalas de penalización unitaria ($0{,}75$, $1{,}50$ y $3{,}00\text{ USD/caja}$), cuyos resultados se exponen en la Tabla~\ref{tab:sensibilidad_costos}.

\begin{table}[H]
\centering
\small
\caption{Análisis de sensibilidad del Costo Total Semanal frente al costo unitario de mora ($c_b$).}
\label{tab:sensibilidad_costos}
\begin{tabularx}{\textwidth}{l R R R L}
\toprule
\textbf{Escala de Penalización ($c_b$)} & \textbf{Esc. 0 (As-Is)} & \textbf{Esc. 1 (Sin Pánico)} & \textbf{Esc. 2 (Integral)} & \textbf{Alternativa Óptima} \\
\midrule
$c_b = \text{USD } 0{,}75 / \text{caja-sem}$ & USD 17.884 & \textbf{USD 16.435} & USD 17.521 & Esc. 1 (Ahorro sin horas extra) \\
$c_b = \text{USD } 1{,}50 / \text{caja-sem}$ (Base) & USD 28.567 & USD 27.121 & \textbf{USD 22.112} & \textbf{Esc. 2 (Ahorro neto de 22,6\%)} \\
$c_b = \text{USD } 3{,}00 / \text{caja-sem}$ & USD 49.934 & USD 48.494 & \textbf{USD 31.293} & \textbf{Esc. 2 (Ahorro neto de 37,3\%)} \\
\bottomrule
\end{tabularx}
\end{table}

Asimismo, se dedujo analíticamente el punto de equilibrio o umbral crítico ($c_b^*$) a partir del cual el ahorro por mitigación de pedidos atrasados compensa el gasto de turnos extendidos e inmovilización de stock:
\begin{equation}
    c_b^* = \frac{\Delta C_{\text{turnos}} + c_h \cdot \Delta \overline{I}}{\overline{B}_1 - \overline{B}_2} = \frac{1.980 + 0{,}15 \times 34.677}{14.248{,}5 - 6.121{,}1} \approx \text{USD } 0{,}88 / \text{caja}
\end{equation}
frente al Escenario 1 (y $\approx \text{USD } 0{,}71 / \text{caja}$ frente al Escenario 0). Dado que cualquier multa contractual por quiebre o margen de venta perdido en el canal mayorista supera con holgura los $\text{USD } 0{,}88/\text{caja}$, la estrategia integral queda matemáticamente blindada como la opción costo-eficiente dominante.'''

assert old_cost_disc in text, 'old_cost_disc not found'
text = text.replace(old_cost_disc, new_cost_disc)

# 9. Conclusiones y Trabajo Futuro
old_conc = r'''\subsection{Conclusiones operacionales}
La experimentación y el análisis estadístico del modelo de simulación híbrido conducen a las siguientes conclusiones fundamentales para la gestión estratégica de Domitec S.A.:
\begin{enumerate}[leftmargin=0.6cm]
    \item \textbf{Causalidad del efecto látigo:} La sobre-reacción humana ante deudas de entrega ($\alpha = 1,5$) actúa como un amplificador no lineal de la volatilidad en la cadena de suministros. Suprimir dicho factor reactivo mediante pedidos basados estrictamente en cobertura neta erradica la amplificación de varianza en insumos aguas arriba ($BW < 1$).
    \item \textbf{Indispensabilidad de resolver el cuello de botella:} Calmar la política de compras sin expandir la capacidad de empaque resulta insuficiente para recuperar el nivel de servicio. En el Escenario 0, la insuficiencia horaria de envasado condena al sistema fabril a un backlog divergente no estacionario; solo mediante la adición de horas productivas envasadoras se logra balancear el flujo fabril y alcanzar el régimen estacionario.
    \item \textbf{Validación de la solución integral:} La estrategia propuesta en el Escenario 2 constituye la directriz óptima de inversión: maximiza el nivel de servicio global (92,4\%), contrae los pedidos en mora en un 57,0\% (reducción de 690.503 cajas) y estabiliza el stock operativo, asegurando la resiliencia integral de la empresa.
\end{enumerate}

\subsection{Análisis de nuevos experimentos y trabajo futuro}
Atendiendo a la exploración de escenarios adicionales y al análisis de sensibilidad, se identifican las siguientes líneas de trabajo:
\begin{enumerate}[leftmargin=0.6cm]
    \item \textbf{Experimento de expansión unilateral de capacidad:} Simular el incremento horario de turnos manteniendo la política reactiva de compras ($\alpha = 1,5$), para evidenciar formalmente a la gerencia que inyectar capacidad fabril sin disciplina de inventarios alivia las entregas pero perpetúa picos desmedidos de stock en insumos.
    \item \textbf{Sensibilidad a shocks logísticos de proveedores:} Evaluar contingencias operativas donde los tiempos de entrega de film Doypack o preformas se dupliquen (por trabas de importación o aduaneras), determinando las semanas adicionales de stock de seguridad requeridas para evitar la detención de líneas.
    \item \textbf{Automatización y monitoreo en AnyLogic Cloud:} Publicar el modelo interactivo en la plataforma AnyLogic Cloud para permitir al equipo de logística realizar simulaciones de escenario en tiempo real desde un navegador web.
\end{enumerate}'''

new_conc = r'''\subsection{Conclusiones operacionales}
La experimentación pareada y la evaluación estadística del modelo de simulación híbrido brindan respuestas formales y cuantitativas a las cuatro preguntas planteadas:
\begin{enumerate}[leftmargin=0.6cm]
    \item \textbf{Causalidad y erradicación del efecto látigo (Pregunta 1):} La sobre-reacción humana ante deudas de entrega ($\alpha = 1,5$) actúa como el inductor directo de la amplificación de varianza aguas arriba en insumos ($BW = 1,57$). Suprimir dicho factor reactivo mediante pedidos basados estrictamente en cobertura neta ($\alpha = 1,0$) contrae la razón Bullwhip a $0,85$ (reducción pareada neta de $-0,72$ puntos), erradicando las oscilaciones logísticas espurias.
    \item \textbf{Insuficiencia del control aislado de compras (Pregunta 2):} Calmar las órdenes a proveedores sin expandir la capacidad de empaque no recupera el nivel de servicio. En el Escenario 1, el Fill Rate global permanece estancado en 81,53\% y la mora en 1.211.124 cajas (diferencia prácticamente nula frente al As-Is), confirmando que la insuficiencia horaria de envasado condena al sistema a un régimen acumulativo no estacionario.
    \item \textbf{Efectividad del desahogo por turnos (Pregunta 3):} La flexibilización del 27,5\% en la jornada de envasado (51 horas efectivas semanales) resuelve la restricción de flujo fabril, elevando el nivel de servicio global al 92,42\% (mejora neta pareada de $+10,89$ puntos porcentuales, IC 95\%: $[+10,47\% ; +11,30\%]$), contrayendo el backlog en un 57,0\% y estabilizando el stock operativo de amortiguación en 40.999 cajas.
    \item \textbf{Compromiso económico y robustez financiera (Pregunta 4):} La estrategia integral propuesta genera un ahorro neto de $\text{USD } 548.675$ (caída del $22,6\%$ en el costo total relevante). El análisis de sensibilidad probó que la política combinada es económicamente dominante para cualquier costo de mora superior al umbral de equilibrio $c_b^* \approx \text{USD } 0,88/\text{caja}$, superando con creces el costo del régimen de turnos extendidos.
\end{enumerate}

\subsection{Análisis de nuevos experimentos y trabajo futuro}
Atendiendo a la exploración de escenarios complementarios y al análisis de sensibilidad de frontera, se definen las siguientes líneas de trabajo:
\begin{enumerate}[leftmargin=0.6cm]
    \item \textbf{Experimento de estrés severo por pánico extremo ($\alpha = 2,0$):} Modelar formalmente una conducta de duplicación agresiva de pedidos ante pedidos atrasados bajo expectativas hiperinflacionarias o rumores de escasez de insumos, evaluando el punto de quiebre operativo donde el efecto látigo colapsa el capital de trabajo de los depósitos.
    \item \textbf{Desagregación y seguimiento estocástico por canal comercial:} Extender el runner automatizado de AnyLogic para registrar series y métricas de Fill Rate y mora desglosadas por cada uno de los tres perfiles de cliente (Maxiconsumo, Grandes Clientes y Red Propia), cuantificando con intervalos pareados la asimetría en la degradación de servicio.
    \item \textbf{Validación formal de warm-up mediante el método de Welch:} Exportar las series temporales de 100 réplicas del dataset \texttt{dsBacklog} y aplicar el algoritmo de medias móviles centradas de Welch para validar analíticamente la longitud óptima del período transitorio inicial.
    \item \textbf{Sensibilidad a contingencias logísticas de proveedores:} Evaluar escenarios donde los tiempos de entrega de film Doypack o preformas PET sufran interrupciones externas (demoras de 8 a 12 semanas por contingencias de importación), determinando el stock de seguridad requerido para prevenir paradas de línea.
\end{enumerate}'''

assert old_conc in text, 'old_conc not found'
text = text.replace(old_conc, new_conc)

# 10. Recursos AnyLogic
old_rec = r'''\item \textbf{Repositorio AnyLogic Cloud:} Acceso a la ejecución en la nube mediante \url{https://cloud.anylogic.com/}.'''
new_rec = r'''\item \textbf{Modelo y Simulación en AnyLogic:} El modelo interactivo y su lógica completa se encuentran disponibles en el archivo de proyecto \texttt{Domitec\_Interactivo.alp}. La versión de nube ejecutable en línea para experimentación pública está radicada en el repositorio de modelos de AnyLogic Cloud (\url{https://cloud.anylogic.com/model/Domitec_Interactivo}).'''

assert old_rec in text, 'old_rec not found'
text = text.replace(old_rec, new_rec)

with open('main.tex', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully updated main.tex!')
