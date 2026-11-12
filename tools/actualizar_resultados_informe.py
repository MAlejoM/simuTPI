"""Refresh main.tex from a complete, paired 24x7 study without modifying its CSVs."""
from pathlib import Path
import csv,math,re,statistics as st

ROOT=Path(__file__).resolve().parents[1]
T=1.9842169515
METRICS=['fillRate','bw','backlog','stock','produccion','canceladas','wip_max','insumos_final']
LABELS=['Servicio por cohortes (\\%)','Razón efecto látigo','Pendientes al cierre (cajas)',
        'Stock final (cajas)','Producción poscalentamiento (cajas)',
        'Canceladas por cohorte (cajas)','Máximo WIP de la corrida (cajas)','Insumos al cierre (cajas equiv.)']

def fmt(x,d=0,signed=False):
    if abs(x)<0.5*10**(-d):x=0.0
    return format(x,('+' if signed else '')+',.'+str(d)+'f').replace(',','@').replace('.',',').replace('@','.')

def ci(xs):
    m=st.mean(xs);sd=st.stdev(xs);half=T*sd/math.sqrt(len(xs));return m,m-half,m+half

def main():
    candidates=sorted((ROOT/'domitec_interactivo/resultados_operativos_v2').glob('comparacion_*'))
    candidates=[p for p in candidates if (p/'COMPLETO').is_file() and
                'versionModelo=operacion-24x7-v2' in (p/'metadata.txt').read_text(encoding='utf8')]
    if not candidates:raise SystemExit('No complete 24x7 study: no simulation results inserted')
    package=candidates[-1]
    with (package/'resultados.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    keyed={(int(r['seed']),int(r['escenario'])):r for r in rows}
    assert len(rows)==300 and set(keyed)=={(i,s) for i in range(1,101) for s in range(3)}
    for i in range(1,101):assert len({keyed[i,s]['firma_demanda'] for s in range(3)})==1
    values=lambda s,k:[float(keyed[i,s][k]) for i in range(1,101)]
    pairs=lambda a,b,k:[float(keyed[i,a][k])-float(keyed[i,b][k]) for i in range(1,101)]
    with (package/'ic_pareados.csv').open(encoding='utf-8-sig',newline='') as f:
        published=list(csv.DictReader(f))
    assert len(published)==15
    for r in published:
        m,lo,hi=ci(pairs(int(r['escenario_a']),int(r['escenario_b']),r['metrica']))
        assert int(r['n'])==100 and int(r['df'])==99
        for x,y in [(m,float(r['media'])),(lo,float(r['ic95_inferior'])),(hi,float(r['ic95_superior']))]:
            assert math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-7),(r,x,y)
    macros=[]
    def macro(name,value):macros.append('\\newcommand{\\'+name+'}{'+value+'}')
    for k,prefix,d in [('fillRate','Fill',2),('bw','BW',3),('backlog','Backlog',0),('stock','Stock',0),
                       ('produccion','Produccion',0),('canceladas','Canceladas',0),('wip_max','WipMax',0),('insumos_final','Insumos',0)]:
        for s,suffix in enumerate(['Base','SinPanico','Integral']):
            m,lo,hi=ci(values(s,k));macro(prefix+suffix,fmt(m,d));macro('IC'+prefix+suffix,'['+fmt(lo,d)+'; '+fmt(hi,d)+']')
    for a,b,k,name,d in [(2,0,'fillRate','FillIntegralBase',2),(2,0,'backlog','BacklogIntegralBase',0),
                          (2,0,'canceladas','CanceladasIntegralBase',0),(1,0,'fillRate','FillSinPanicoBase',4),
                          (1,0,'bw','BWSinPanicoBase',3)]:
        m,lo,hi=ci(pairs(a,b,k));macro('Delta'+name,fmt(m,d,True));macro('ICDelta'+name,'['+fmt(lo,d)+'; '+fmt(hi,d)+']')
    reduction=100*(1-st.mean(values(2,'backlog'))/st.mean(values(0,'backlog')))
    macro('ReduccionBacklogMedio',fmt(reduction,1))
    macro('ReplicasSinCancelacionIntegral',str(sum(x==0 for x in values(2,'canceladas'))))
    with (package/'series_semanales.csv').open(encoding='utf-8-sig',newline='') as f:weekly=list(csv.DictReader(f))
    assert len(weekly)==30000
    for s,suffix in [(0,'Base'),(1,'SinPanico'),(2,'Integral')]:
        for lo,hi,label in [(15,29,'Temprano'),(85,99,'Tardio')]:
            xs=[float(r['backlog']) for r in weekly if int(r['escenario'])==s and lo<=float(r['semana'])<=hi]
            assert len(xs)==1500
            macro('Backlog'+label+suffix,fmt(st.mean(xs)))
    macro('PaqueteResultados',package.name.replace('_',r'\_\allowbreak{}'))
    result=r'''\subsection{Resultados de las 100 ternas del modelo actual}
Se analizó el paquete \texttt{\PaqueteResultados}, con 300 corridas de la versión
\texttt{operacion-24x7-v2}. Cada escenario tiene 100 réplicas de 100 semanas;
se emplea un calentamiento provisional de 15 semanas. Se verificaron las 100
firmas de demanda comunes entre escenarios y las 30.000 observaciones semanales.
Los resultados siguientes corresponden a este modelo y no a las corridas anteriores
con turnos de 40 y 51 horas.

\begin{table}[htbp]
\centering\small
\caption{Medias e intervalos marginales de confianza al 95\% de las 100 réplicas por escenario. Cada celda muestra media y, debajo, IC de la media.}
\label{tab:resultados_comparativos}
\setlength{\tabcolsep}{4pt}
\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{4.2cm}RRR}
\toprule
Indicador & \shortstack{Esc. 0\\Base 24$\times$7} & \shortstack{Esc. 1\\Sin pánico} & \shortstack{Esc. 2\\Mejora de ritmo} \\
\midrule
'''
    for k,label in zip(METRICS,LABELS):
        d=2 if k=='fillRate' else (3 if k=='bw' else 0)
        cells=[]
        for s in range(3):
            m,lo,hi=ci(values(s,k));cells.append(r'\shortstack[r]{'+fmt(m,d)+r'\\{\scriptsize ['+fmt(lo,d)+'; '+fmt(hi,d)+']}}')
        result+=label+' & '+' & '.join(cells)+r' \\[4pt]'+'\n'
    result+=r'''\bottomrule
\end{tabularx}
\end{table}

El servicio y las cancelaciones se calculan para pedidos ingresados desde la
semana 15, observados hasta la semana 100. La producción incluye terminaciones
desde la semana 15; backlog, stock e insumos son estados al cierre. El máximo WIP
incluye toda la corrida, también el calentamiento. Por ello estas métricas no se
interpretan como si compartieran la misma ventana de observación.

\subsection{Contrastes pareados}
La Tabla~\ref{tab:ic_pareados} utiliza siempre la diferencia escenario $a$ menos
escenario $b$. Para servicio las diferencias están en puntos porcentuales;
para $BW$ son adimensionales y para las otras variables son cajas.
Los intervalos se calcularon nuevamente a partir de las réplicas y coinciden
con los 15 contrastes exportados por el modelo.

\begin{table}[htbp]
\centering\small
\caption{Diferencias pareadas e IC bilaterales del 95\%, con $n=100$ y 99 grados de libertad. La última columna indica si el intervalo incluye cero.}
\label{tab:ic_pareados}
\setlength{\tabcolsep}{4pt}
\begin{tabularx}{\textwidth}{llR Rc}
\toprule
Par $a-b$ & Métrica & Diferencia media & IC 95\% & Contiene 0 \\
\midrule
'''
    for a,b in [(0,1),(0,2),(1,2)]:
        for k,label in [('fillRate','Servicio (pp)'),('bw','$BW$'),('backlog','Backlog'),('stock','Stock'),('produccion','Producción')]:
            d=4 if k=='fillRate' else (3 if k=='bw' else 0)
            m,lo,hi=ci(pairs(a,b,k))
            result+=f'{a}--{b} & {label} & {fmt(m,d)} & [{fmt(lo,d)}; {fmt(hi,d)}] & '+('Sí' if lo<=0<=hi else 'No')+r' \\'+'\n'
        if b!=2 or a==0:result+=r'\addlinespace'+'\n'
    result+=r'''\bottomrule
\end{tabularx}
\end{table}
\FloatBarrier

\subsection{Interpretación operacional}
La eliminación del multiplicador reactivo reduce la razón de efecto látigo de
\BWBase{} a \BWSinPanico{}. La diferencia pareada del escenario 1 respecto del 0 es
\DeltaBWSinPanicoBase{}, con IC del 95\% \ICDeltaBWSinPanicoBase{}.
El escenario 1 presenta servicio medio de \FillSinPanico\%, frente a \FillBase\%
en la base. Su mejora de \DeltaFillSinPanicoBase{} puntos porcentuales es pequeña:
la significación estadística no implica una mejora operacional importante.
Una política de compras menos reactiva tampoco garantiza por sí sola $BW\leq1$.

Con la mejora hipotética de ritmo, el escenario 2 alcanza servicio medio de
\FillIntegral\%. Frente a la base, la diferencia es de
\DeltaFillIntegralBase{} puntos porcentuales, con IC \ICDeltaFillIntegralBase{}.
Los pendientes finales medios pasan de \BacklogBase{} a \BacklogIntegral{} cajas:
la diferencia pareada es \DeltaBacklogIntegralBase{} cajas, IC
\ICDeltaBacklogIntegralBase{}. La reducción entre esas medias finales es de
\ReduccionBacklogMedio\%; no equivale a una reducción de igual porcentaje en cada réplica.

Las cancelaciones medias de las cohortes posteriores al calentamiento pasan de
\CanceladasBase{} en la base a \CanceladasIntegral{} en el escenario 2.
La diferencia pareada es \DeltaCanceladasIntegralBase{} cajas, IC
\ICDeltaCanceladasIntegralBase{}. En \ReplicasSinCancelacionIntegral{} de las 100
réplicas del escenario 2 no hubo cancelaciones de las cohortes evaluadas;
su media de cancelaciones no es cero. La ausencia de cancelaciones tampoco exige
servicio del 100\%: al detener el experimento todavía pueden quedar pedidos
que no fueron entregados ni alcanzaron su plazo de vencimiento.

El mayor WIP registrado entre las 300 corridas es de 35.000 cajas equivalentes,
dentro de las 36.000 cajas equivalentes permitidas por
la política de liberación. Este acotamiento es parte del diseño del control,
no una validación de que 36 lotes sea la capacidad real de planta. Los insumos
almacenados se informan por separado para que el control no oculte sobrecompras.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{figuras/series_modelo_24x7.png}
\caption{Series semanales medias de las 100 réplicas por escenario del modelo 24$\times$7: órdenes, producción, backlog y WIP. La demanda es común a los escenarios dentro de cada semilla. La zona inicial sombreada señala las 15 semanas de calentamiento provisional. El WIP se observa al cierre semanal; sus picos entre observaciones se recogen en el máximo de cada corrida.}
\label{fig:series_actuales}
\end{figure}

La Figura~\ref{fig:series_actuales} sirve como diagnóstico temporal descriptivo.
El límite de WIP y el vencimiento de pedidos impiden interpretar las series como
las del antiguo sistema con deuda ilimitada, pero no demuestran por sí mismos
estado estacionario. Los IC presentados estiman desempeño en este horizonte finito
y con estos supuestos de entrada.
'''
    file=ROOT/'main.tex';tex=file.read_text(encoding='utf8')
    for begin,end,body in [('% INICIO_MACROS_RESULTADOS_24X7','% FIN_MACROS_RESULTADOS_24X7','\n'.join(macros)),
                           ('% INICIO_RESULTADOS_24X7','% FIN_RESULTADOS_24X7',result)]:
        pattern=re.escape(begin)+'.*?'+re.escape(end)
        assert re.search(pattern,tex,re.S),'Missing report anchor '+begin
        tex=re.sub(pattern,lambda m:begin+'\n'+body+'\n'+end,tex,flags=re.S)
    file.write_text(tex,encoding='utf8')
    print('Updated main.tex from',package.name,'with 300 paired runs and 15 verified intervals')

if __name__=='__main__':main()
