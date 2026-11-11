"""Apply the reviewed 24x7 runtime to the existing model; preserve presentation and editor changes."""
from pathlib import Path
from xml.dom import minidom as D
import re, shutil, tempfile, sys
from crear_interfaz import children, text, put, code

ROOT=Path(__file__).resolve().parents[1]

def configurar_escenarios_simulacion(d):
    """Pass an explicit scenario before Main starts; alpha=1 alone cannot identify 1 vs 2."""
    model=children(d.documentElement,'Model')[0]
    scenarios={'Simulation_Escenario0_AsIs':0,'Simulation_Escenario1_SinPanico':1,
               'Simulation_Escenario2_Integral':2}
    for experiment in children(children(model,'Experiments')[0]):
        name=text(experiment,'Name')
        if name not in scenarios:continue
        scenario=scenarios[name]
        params=children(experiment,'Parameters')[0]
        values={'numeroEscenario':str(scenario),'factorLatigoMain':'1.5' if scenario==0 else '1.0',
                'escalaTurnoMain':'1.0','esComparacion':'false'}
        for key,value in values.items():
            p=next((p for p in children(params) if text(p,'ParameterName')==key),None)
            if p is None:p=d.createElement('Parameter');put(p,'ParameterName',key);params.appendChild(p)
            val=children(p,'ParameterValue')
            if not val:val=[d.createElement('ParameterValue')];p.appendChild(val[0])
            val[0].setAttribute('Class','CodeValue');code(val[0],'Code',value)

def recalibrar(d):
    model=children(d.documentElement,'Model')[0]
    agents={text(a,'Name'):a for a in children(children(model,'ActiveObjectClasses')[0])}
    main,plant=agents['Main'],agents['DomitecPlant']
    uid=max(int(n.firstChild.data) for n in d.getElementsByTagName('Id') if n.firstChild and n.firstChild.data.isdigit())+100
    def fresh(node):
        nonlocal uid
        for n in [node]+list(node.getElementsByTagName('*')):
            if n.tagName=='Id':uid+=1;n.firstChild.data=str(uid)
    def var(name,typ,default):
        container=children(main,'Variables')[0]
        n=next((n for n in children(container) if text(n,'Name')==name),None)
        if n is None:
            n=next(n for n in children(container) if text(n,'Name')=='uiWarmup').cloneNode(True)
            fresh(n);put(n,'Name',name);container.appendChild(n)
        prop=children(n,'Properties')[0];put(prop,'Type',typ)
        value=children(prop,'InitialValue') or children(prop,'DefaultValue')
        code(value[0],'Code',default)
        put(n,'PresentationFlag','false');put(n,'ShowLabel','false');put(n,'X',2300);put(n,'Y',1400)
    var('uiEspera','double','30');var('uiMaxWip','int','36')
    for name,default in [('uiHoras','168'),('uiMermaLav','0'),('uiMermaLiq','0'),('escalaTurnoMain','1.0'),('uiRate','DatosOperativos.rates()[0]'),
                         ('uiMedia','DatosOperativos.medias()[0][0]'),('uiDesvio','DatosOperativos.desvios()[0][0]'),
                         ('carpetaResultados','java.nio.file.Paths.get(System.getProperty("user.dir"),"resultados_operativos_v2").toAbsolutePath().toString()')]:
        n=next(n for n in children(children(main,'Variables')[0]) if text(n,'Name')==name)
        prop=children(n,'Properties')[0];value=children(prop,'InitialValue') or children(prop,'DefaultValue');code(value[0],'Code',default)
    additional=(ROOT/'tools/MainInterfaz.code.java.txt').read_text(encoding='utf8')
    additional=re.sub(r'^public (?:double uiMedia|double uiLatigo|int uiReactores|double uiEspera|int uiMaxWip|String carpetaResultados).*?;\n','',additional,flags=re.M)
    code(main,'AdditionalClassCode',additional)
    code(plant,'AdditionalClassCode',(ROOT/'tools/PlantaControl.code.java.txt').read_text(encoding='utf8'))
    code(children(plant,'AgentProperties')[0],'OnReceive',(ROOT/'tools/PlantaRecepcion.code.java.txt').read_text(encoding='utf8'))
    events={text(n,'Name'):n for n in children(children(plant,'Events')[0])}
    code(events['avanceProduccion'],'Action','operarPlanta();')
    put(events['avanceProduccion'],'ExcludeFromBuild','false')
    code(events['planificacionSemanal'],'Action',(ROOT/'tools/PlanificacionSemanal.code.java.txt').read_text(encoding='utf8'))
    startup=text(plant,'StartupCode')
    startup=re.sub(r'for \(ProductState ps : inventorySystem\) \{\s*productionLines.add\(new ProductionLineState\(ps.product\)\);\s*\}', '',startup)
    code(plant,'StartupCode',startup)
    blocks={text(b,'Name'):b for b in children(children(plant,'EmbeddedObjects')[0])}
    def parameter(block,name,value,unit=None):
        params=children(blocks[block],'Parameters')[0]
        p=next(n for n in children(params) if text(n,'Name')==name)
        values=children(p,'Value')
        if not values:values=[d.createElement('Value')];p.appendChild(values[0])
        v=values[0];v.setAttribute('Class','CodeUnitValue' if unit else 'CodeValue');code(v,'Code',value)
        if unit:
            put(v,'Unit',unit);children(v,'Unit')[0].setAttribute('Class','TimeUnits')
    # All process delays return calendar weeks. No extra 168/40 multiplier.
    for name,b in blocks.items():
        if name.startswith('delay'):
            p=next(n for n in children(children(b,'Parameters')[0]) if text(n,'Name')=='delayTime')
            parameter(name,'delayTime',text(children(p,'Value')[0],'Code'),'WEEK')
            capacity='controlador().cfg.reactores' if name=='delayReactoresLiquidos' else ('2' if name=='delayQCLiquidos' else '1')
            parameter(name,'capacity',capacity);parameter(name,'maximumCapacity','false')
        if name.startswith('queue') or name.startswith('tank'):
            capacity='controlador().cfg.tanque' if name.startswith('tank') or name=='queueTanquePulmon' else 'controlador().cfg.cola'
            parameter(name,'capacity',capacity);parameter(name,'maximumCapacity','false')
    # Every released batch returns its card once, whether good or scrapped.
    for name,scrap in [('sinkTerminado',False),('sinkLiquidosTerminados',False),('sinkScrapLavandina',True),('sinkScrapLiquidos',True)]:
        p=next(n for n in children(children(blocks[name],'Parameters')[0]) if text(n,'Name')=='onEnter')
        value=children(p,'Value')[0];body=text(value,'Code')
        body=re.sub(r'^finalizarLote\(agent,(?:true|false)\);\s*','',body)
        code(value,'Code',f'finalizarLote(agent,{str(scrap).lower()});\n'+body)
    classes=children(model,'JavaClasses')[0]
    for name in ['ConfiguracionDomitec','ComparacionEscenarios','RegistroCorrida','EstudioPareado','SesionEstudio',
                 'CalendarioPlanta','BalanceMateriales','DatosOperativos']:
        n=next((n for n in children(classes) if text(n,'Name')==name),None)
        if n is None:
            n=next(n for n in children(classes) if text(n,'Name')=='ConfiguracionDomitec').cloneNode(True)
            fresh(n);put(n,'Name',name);classes.appendChild(n)
        code(n,'Text',(ROOT/'tools'/f'{name}.java').read_text(encoding='utf8'))
    # Add the two explicit assumptions in unused space of the left logic card.
    scene=children(children(children(main,'Presentation')[0],'Level')[0],'Presentation')[0]
    def named(name):return next(n for n in scene.getElementsByTagName('*') if text(n,'Name')==name)
    logic=children(named('cuerpoVista3'),'Presentation')[0]
    def label(name,y,title):
        n=next((n for n in children(logic) if text(n,'Name')==name),None)
        if n is None:n=named('mediaLabel').cloneNode(True);fresh(n);put(n,'Name',name);logic.appendChild(n)
        put(n,'X',56);put(n,'Y',y);put(n,'Text',title)
        if children(n,'TextCode'):n.removeChild(children(n,'TextCode')[0])
        return n
    def edit(name,y,link):
        n=next((n for n in children(logic) if text(n,'Name')==name),None)
        if n is None:n=named('campoWarmup').cloneNode(True);fresh(n);put(n,'Name',name);logic.appendChild(n)
        put(n,'X',56);put(n,'Y',y);children(n,'BasicProperties')[0].setAttribute('Width','320')
        put(children(n,'ExtendedProperties')[0],'Link',link)
    put(named('notaDemandaUI'),'Y',610)
    put(named('notaDemandaUI'),'Text','Meses de 2025 remuestreados.\nVariacion mensual; no mide picos diarios.')
    label('esperaLabel',657,'Cancelacion: espera SUPUESTA (dias)');edit('campoEspera',680,'uiEspera')
    label('maxWipLabel',727,'Limite PROVISIONAL de lotes liberados');edit('campoMaxWip',750,'uiMaxWip')
    for n in scene.getElementsByTagName('Text'):
        title=text(n,'Text')
        if title=='Horas operativas / semana':put(n,'Text','Horas de apertura / semana (max. 168)')
        if title.startswith('Envasado (cajas/h'):put(n,'Text','Ritmo efectivo (cajas/h de apertura)')
        if title.startswith('Rechazo lavandina'):put(n,'Text','Rechazo adicional lavandina (%)')
        if title.startswith('Rechazo liquidos'):put(n,'Text','Rechazo adicional liquidos (%)')
    for button_name,title in [('escenarioUI0','0 - Base 24x7'),('escenarioUI1','1 - Sin panico'),('escenarioUI2','2 - Rendimiento +27.5%')]:
        try:put(children(named(button_name),'ExtendedProperties')[0],'LabelText',title)
        except StopIteration:pass
    for n in scene.getElementsByTagName('Control'):
        bp=children(n,'BasicProperties')
        if not bp:continue
        action=text(bp[0],'ActionCode').replace(' ','')
        if action=='elegirEscenario(0);':put(children(n,'ExtendedProperties')[0],'LabelText','0 - Base 24x7')
        if action=='elegirEscenario(2);':put(children(n,'ExtendedProperties')[0],'LabelText','2 - Rendim. +27.5%')
    summary=next((n for n in children(scene) if text(n,'Name')=='resumenOperacionUI'),None)
    if summary is None:summary=named('mensajeUItexto').cloneNode(True);fresh(summary);put(summary,'Name','resumenOperacionUI');scene.appendChild(summary)
    put(summary,'X',24);put(summary,'Y',978);put(children(summary,'Font')[0],'Size',12)
    put(summary,'Text','Operacion 24x7')
    code(summary,'TextCode','"24x7 | Canceladas: "+numero(canceladasActual())+" | Insumos almacenados: "+numero(insumosActual())+" | WIP liberado: "+numero(wipActual())')
    # Legacy parameters no longer dictate operating time.
    param_id=next(text(n,'Id') for n in children(children(main,'Variables')[0]) if text(n,'Name')=='escalaTurnoMain')
    for experiment in children(children(model,'Experiments')[0]):
        for n in children(experiment,'FreeformParamValue'):
            if text(n,'Id')==param_id and children(n,'Expression'):code(children(n,'Expression')[0],'Code','1.0')
    from documentar_planta import documentar
    documentar(d)
    configurar_escenarios_simulacion(d)

def main():
    backup=Path(tempfile.mkdtemp(prefix='domitec-antes-operacion-24x7-'))
    for path in (ROOT/'domitec_interactivo').glob('Domitec_Interactivo.alp*'):
        if path.suffix not in ['.alp','.autosave']:continue
        shutil.copy2(path,backup/path.name)
        d=D.parse(str(path))
        if '--solo-escenarios' in sys.argv:configurar_escenarios_simulacion(d)
        else:recalibrar(d)
        path.write_bytes(d.toxml(encoding='UTF-8'))
        print('Updated',path.name)
    print('Backup:',backup)

if __name__=='__main__':main()
