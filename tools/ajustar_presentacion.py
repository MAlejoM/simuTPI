"""Refine the existing UI, preserving business logic and backing up editor files."""
from pathlib import Path
from xml.dom import minidom as D
import math, re, shutil, tempfile
from crear_interfaz import children, text, put, code
from plano_2d import crear_plano

ROOT = Path(__file__).resolve().parents[1]

def ajustar(d):
    model = children(d.documentElement,'Model')[0]
    agents = {text(a,'Name'):a for a in children(children(model,'ActiveObjectClasses')[0],'ActiveObjectClass')}
    main, plant = agents['Main'], agents['DomitecPlant']
    # Hide model-element icons, preserving their IDs, connections and behavior.
    for a in agents.values():
        for tag in ['Variables','Ports','Connectors','Events','AnalysisData','DynamicEvents']:
            for container in children(a,tag):
                for n in children(container):
                    put(n,'PresentationFlag','false'); put(n,'ShowLabel','false')
    # Keep the editable logic alongside the panel, outside its viewport.
    for tag in ['Variables','Connectors','Events','AnalysisData','EmbeddedObjects']:
        for container in children(main,tag):
            for n in children(container):
                if children(n,'X') and float(text(n,'X')) < 1500:
                    put(n,'X',float(text(n,'X'))+1600)
                    put(n,'Y',float(text(n,'Y'))+1200)
                if tag=='EmbeddedObjects':
                    put(n,'PresentationFlag','false');put(n,'ShowLabel','false')
    # Receiving a delivery must not override the user's simulation speed.
    receipt=children(plant,'AgentProperties')[0]
    body=text(receipt,'OnReceive')
    body=re.sub(r'boolean primeraEntregaVisual = animacionLavandina\.recibir\(time\(\), delivery\.amount\);\s*if \(primeraEntregaVisual && getEngine\(\)\.getRealTimeMode\(\)\) \{\s*//[^\n]*\n\s*getEngine\(\)\.setRealTimeScale\(1\.0 / 672\.0\);\s*\}',
                'animacionLavandina.recibir(time(), delivery.amount);',body)
    code(receipt,'OnReceive',body)
    assert 'setRealTimeScale' not in body
    additional=(ROOT/'tools/MainInterfaz.code.java.txt').read_text(encoding='utf8')
    additional=re.sub(r'^public (?:double uiMedia|double uiLatigo|int uiReactores|String carpetaResultados).*?;\n','',additional,flags=re.M)
    code(main,'AdditionalClassCode',additional)
    scene=children(children(children(main,'Presentation')[0],'Level')[0],'Presentation')[0]
    def byname(name):return next(n for n in scene.getElementsByTagName('*') if text(n,'Name')==name)
    # Text is anchored at its top edge. Leave a full caption height above inputs.
    for n in scene.getElementsByTagName('Text'):put(n,'Alignment','LEFT')
    for n in scene.getElementsByTagName('Control'):
        if n.getAttribute('Type')=='EditBox':
            name=text(n,'Name');caption={'campoMedia':'mediaLabel','campoDesvio':'sdLabel'}.get(name,name+'Label')
            if name=='campoTanque':caption='tanqueLabel'
            if name!='campoCarpeta':put(n,'Y',float(text(byname(caption),'Y'))+25)
            basic=children(n,'BasicProperties')[0];basic.setAttribute('Height','30')
            for font in children(children(n,'ExtendedProperties')[0],'Font'):
                font.setAttribute('Name','SansSerif');font.setAttribute('Size','13')
    for name,y in {'marcaUI':19,'tituloVista':89,'tituloEscenarios':89,'tituloParametros':89,
                   'tituloDemandaUI':237,'tituloInventarioUI':237,'tituloProcesoUI':237,
                   'rutaCSVLabel':858}.items():put(byname(name),'Y',y)
    for i in range(6):
        put(byname('kpiTitulo'+str(i)),'Y',922);put(byname('kpiValor'+str(i)),'Y',944)
    # A shared action row below the three cards, clear of their borders/inputs.
    for name in ['card_demanda','card_inventario','card_proceso']:put(byname(name),'Height',576)
    apply_button=byname('aplicarPlantaUI')
    put(apply_button,'X',430);put(apply_button,'Y',811)
    children(apply_button,'BasicProperties')[0].setAttribute('Width','804')
    for name in ['mediaLabel','sdLabel','tanqueLabel']+[text(n,'Name') for n in scene.getElementsByTagName('Text') if text(n,'Name').startswith('campo')]:
        for font in children(byname(name),'Font'):put(font,'Size',12)
    # The 2D tab owns its diagram; it never projects 3D meshes into the panel.
    g=children(byname('cuerpoVista0'),'Presentation')[0]
    rect=byname('fondoUI').cloneNode(True);txt=byname('mediaLabel').cloneNode(True)
    ids=[int(n.firstChild.data) for n in d.getElementsByTagName('Id') if n.firstChild and n.firstChild.data.strip().isdigit()]
    uid=max(ids)+1
    def fresh(n):
        nonlocal uid
        for idnode in n.getElementsByTagName('Id'):
            while idnode.firstChild:idnode.removeChild(idnode.firstChild)
            uid+=1;idnode.appendChild(d.createTextNode(str(uid)))
    def panel(parent,name,x,y,w,h,color,line=None):
        n=rect.cloneNode(True);fresh(n)
        for old in list(children(n)):
            if old.tagName.endswith('Code'):n.removeChild(old)
        for key,val in {'Name':name,'X':x,'Y':y,'Width':w,'Height':h,'FillColor':color,'LineColor':color if line is None else line,'LineWidth':0 if line is None else 1}.items():put(n,key,val)
        parent.appendChild(n);return n
    def label(parent,name,x,y,value,size=12,color=-14340540,expr=None):
        n=txt.cloneNode(True);fresh(n)
        for old in list(children(n)):
            if old.tagName.endswith('Code'):n.removeChild(old)
        for key,val in {'Name':name,'X':x,'Y':y,'Text':value,'Color':color,'Alignment':'LEFT'}.items():put(n,key,val)
        put(children(n,'Font')[0],'Size',size)
        if expr:code(n,'TextCode',expr)
        parent.appendChild(n);return n
    while g.firstChild:g.removeChild(g.firstChild)
    crear_plano(g,panel,label)

    # Export the floor, roads and markings along with the public 3D models.
    plant_scene=children(children(children(plant,'Presentation')[0],'Level')[0],'Presentation')[0]
    for n in plant_scene.getElementsByTagName('*'):
        # EmbeddedIcon routes a shape to the agent's 2D icon, not its scene.
        if children(n,'EmbeddedIcon'):put(n,'EmbeddedIcon','false')
        if n.tagName in ['Rectangle','Group'] and text(n,'DrawMode') in ['SHAPE_DRAW_3D','SHAPE_DRAW_2D3D']:
            put(n,'PublicFlag','true');put(n,'DrawMode','SHAPE_DRAW_3D')
        if n.tagName=='Rectangle' and text(n,'Name') in ['bg_sector_parque','bg_sector_vicentin']:
            put(n,'Z',0.45);put(n,'ZHeight',0.1)
    camera=byname('camaraMain')
    for k,v in {'X':920,'Y':605+1300/math.tan(math.radians(55)),'Z':1300,'RotationX':55,'RotationZ':-90}.items():put(camera,k,v)
    window=byname('ventanaPlanta3D');put(window,'Y',244);put(window,'Height',653)
    body3=children(byname('cuerpoVista1'),'Presentation')[0]
    if not any(text(n,'Name')=='tituloPlanta3D' for n in children(body3)):
        label(body3,'tituloPlanta3D',40,214,'PLANTA 3D | Vista general',13,-14381747)
        button=byname('editarLogicaUI').cloneNode(True);fresh(button)
        for k,v in {'Name':'restablecerCamaraUI','X':1036,'Y':207}.items():put(button,k,v)
        bp=children(button,'BasicProperties')[0];bp.setAttribute('Width','196');code(bp,'ActionCode','restablecerCamara();')
        put(children(button,'ExtendedProperties')[0],'LabelText','Restablecer camara');body3.appendChild(button)
    if not any(text(n,'Name')=='vistaSuperiorUI' for n in children(body3)):
        button=byname('restablecerCamaraUI').cloneNode(True);fresh(button)
        for k,v in {'Name':'vistaSuperiorUI','X':820,'Y':207}.items():put(button,k,v)
        bp=children(button,'BasicProperties')[0];bp.setAttribute('Width','204');code(bp,'ActionCode','vistaSuperior();')
        put(children(button,'ExtendedProperties')[0],'LabelText','Vista superior');body3.appendChild(button)

    # Short-lived WIP is sampled hourly in the visual simulation, on its own axis.
    event_container=children(main,'Events')[0]
    weekly_sampler=next(n for n in children(event_container) if text(n,'Name')=='observarSemana')
    # Keep the last observation farther from t=100 than the engine's 1e-5 TTOL.
    code(children(children(weekly_sampler,'Properties')[0],'OccurrenceTime')[0],'Code','0.9999')
    if not any(text(n,'Name')=='muestrearWip' for n in children(event_container)):
        sampler=next(n for n in children(event_container) if text(n,'Name')=='observarSemana').cloneNode(True);fresh(sampler)
        for k,v in {'Name':'muestrearWip','X':2100,'Y':1600,'PresentationFlag':'false','ShowLabel':'false'}.items():put(sampler,k,v)
        code(sampler,'Action','actualizarWipGrafico();');props=children(sampler,'Properties')[0]
        for tag,value in [('Timeout','1'),('OccurrenceTime','0'),('RecurrenceCode','1')]:
            node=children(props,tag)[0];code(node,'Code',value);children(node,'Unit')[0].firstChild.data='HOUR'
        event_container.appendChild(sampler)
    ds=next(n for n in children(children(main,'AnalysisData')[0]) if text(n,'Name')=='dsWip')
    put(ds,'SamplesToKeep',20000)
    weekly=next(n for n in children(children(plant,'Events')[0]) if text(n,'Name')=='planificacionSemanal')
    code(weekly,'Action',text(weekly,'Action').replace('m.dsWip.add(time(), totalWip);','// WIP visual: hourly sampling in Main; no weekly aliasing.'))
    plot=byname('plot2');stats=children(byname('cuerpoVista2'),'Presentation')[0]
    wip_plot=next((n for n in children(stats) if text(n,'Name')=='plotWip'),None)
    if wip_plot is None:
        wip_plot=plot.cloneNode(True);fresh(wip_plot);put(wip_plot,'Name','plotWip');stats.appendChild(wip_plot)
    for n,name,x,expression in [(plot,'plot2',40,'dsBacklog'),(wip_plot,'plotWip',446,'dsWip')]:
        put(n,'X',x);put(n,'Width',384);put(children(n,'ChartArea')[0],'Width',306)
        for ds_expr in list(children(n,'DatasetExpression')):
            if text(ds_expr,'Expression')!=expression:n.removeChild(ds_expr)
            else:
                put(ds_expr,'LineWidth',2.5)
                if expression=='dsWip':put(ds_expr,'Color',-7453523);put(ds_expr,'Title','Cajas en proceso (WIP)')
    put(byname('tituloStats'),'Text','ESTADISTICAS | Series de las 100 semanas')
    put(children(byname('estudioUI'),'ExtendedProperties')[0],'LabelText','Guardar parametros para estudio')
    put(children(byname('detenerEstudioUI'),'ExtendedProperties')[0],'LabelText','Leer ultimos IC')
    code(children(byname('detenerEstudioUI'),'BasicProperties')[0],'ActionCode','cargarUltimosIC();')

    # Experiments must be launched by AnyLogic, rather than nested in a live run.
    for name in ['SesionEstudio','EstudioPareado','OperarioAnimation']:
        helper=next(n for n in children(children(model,'JavaClasses')[0]) if text(n,'Name')==name)
        code(helper,'Text',(ROOT/'tools'/f'{name}.java').read_text(encoding='utf8'))
    study=next(n for n in children(children(model,'Experiments')[0]) if text(n,'Name')=='Comparacion_100x3')
    code(study,'AdditionalClassCode','public EstudioPareado estudio=new EstudioPareado();\n{ SesionEstudio.usarPredeterminados(); }')
    configid=next(text(n,'Id') for n in children(children(main,'Variables')[0]) if text(n,'Name')=='configuracionInicial')
    configparam=next(n for n in children(study,'FreeformParamValue') if text(n,'Id')==configid)
    expression=children(configparam,'Expression')[0];code(expression,'Code','SesionEstudio.configuracionPreparada()')
    code(study,'AfterSimulationRunCode','''try {
    root.validarCorridaCompleta();
    if(root.semillaReplica==1 && root.numeroEscenario==0)estudio=new EstudioPareado();
    estudio.agregar(root.resultadoFinal(root.numeroEscenario),root.registro.firmaDemanda(),root.registro.seriesCsv(root.semillaReplica,root.numeroEscenario),root.cfg.calentamiento,root.cfg,SesionEstudio.carpetaEnCurso);
} catch(RuntimeException error) {
    SesionEstudio.finalizar(error.getMessage());
    if(estudio.getCount()==300 && !estudio.isTerminado()) {
        SesionEstudio.estado="300 corridas completas. Guardado pendiente: " + error.getMessage();
        SesionEstudio.ultimoResumen="Pulsar Reintentar guardado; se conservan los resultados en memoria.";
    } else throw error;
}''')
    ep=children(study,'Presentation')
    if not ep:ep=[d.createElement('Presentation')];study.appendChild(ep[0])
    while ep[0].firstChild:ep[0].removeChild(ep[0].firstChild)
    panel(ep[0],'fondoEstudio',0,0,1280,1010,-658189)
    label(ep[0],'tituloEstudio',40,40,'DOMITEC | COMPARACION 100 x 3',25,-14381747)
    label(ep[0],'disenoEstudio',40,100,'100 semillas. Tres escenarios por semilla. Horizonte: 100 semanas.',17)
    label(ep[0],'instruccionEstudio',40,145,'Podes ejecutar directamente con los valores predeterminados. Guardar parametros desde Main es opcional.',14)
    for name,x,w,title,action in [
        ('ejecutarDefault',40,310,'Ejecutar predeterminados','SesionEstudio.usarPredeterminados();run();'),
        ('ejecutarGuardados',370,310,'Usar guardados y ejecutar','try{SesionEstudio.cargarConfiguracionGuardada();run();}catch(RuntimeException e){getExperimentHost().showMessageDialog(e.getMessage());}'),
        ('reintentarGuardado',700,310,'Reintentar guardado','try{estudio.reintentarExportacion(SesionEstudio.carpetaEnCurso);}catch(RuntimeException e){getExperimentHost().showMessageDialog(e.getMessage());}')]:
        button=byname('editarLogicaUI').cloneNode(True);fresh(button)
        for k,v in {'Name':name,'X':x,'Y':195}.items():put(button,k,v)
        bp=children(button,'BasicProperties')[0];bp.setAttribute('Width',str(w));code(bp,'ActionCode',action)
        put(children(button,'ExtendedProperties')[0],'LabelText',title);ep[0].appendChild(button)
    label(ep[0],'progresoEstudio',40,270,'Progreso',19,expr='"Corridas completas: " + SesionEstudio.progreso + " / 300"')
    label(ep[0],'estadoEstudio',40,325,'Estado',14,expr='SesionEstudio.estado')
    label(ep[0],'resumenEstudio',40,395,'Resumen',13,expr='SesionEstudio.ultimoResumen')
    label(ep[0],'carpetaEstudio',40,475,'Carpeta',13,expr='"Resultados: " + SesionEstudio.carpetaEnCurso')
    label(ep[0],'notaEstudio',40,545,'Al finalizar, volver a Main > Estadisticas > Leer ultimos IC.\nSi falla el guardado, mantener esta ventana abierta y pulsar Reintentar guardado.\nStop interrumpe el lote; solo se publican paquetes con el marcador COMPLETO.',14)
    from documentar_planta import documentar
    documentar(d)
    # Apply the current operating model last, so visual rebuilds cannot restore
    # the former 40-hour clock, unlimited queues or permanent backlog.
    from recalibrar_operacion import recalibrar
    recalibrar(d)

def main():
    backup=Path(tempfile.mkdtemp(prefix='domitec-antes-orden-visual-'))
    for p in (ROOT/'domitec_interactivo').glob('Domitec_Interactivo.alp*'):
        if p.suffix not in ['.alp','.autosave']:continue
        shutil.copy2(p,backup/p.name)
        d=D.parse(str(p));ajustar(d);p.write_bytes(d.toxml(encoding='UTF-8'))
        print('Updated',p.name)
    print('Backup:',backup)

if __name__=='__main__':main()
