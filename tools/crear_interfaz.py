"""Author the live four-tab UI and paired CRN experiments in a new model.

The previous model/autosave is never overwritten. Source and assets are copied;
all changes to stochastic behavior and measured windows are documented separately.
"""
from pathlib import Path
from xml.dom import minidom as D
import json, re, shutil, subprocess, zipfile, sys

ROOT=Path(__file__).resolve().parents[1]
SOURCE_DIR=ROOT/'main_con_3d'
OUT=ROOT/'domitec_interactivo'
OUTPUT=OUT/'Domitec_Interactivo.alp'

def children(n,tag=None):return [c for c in n.childNodes if c.nodeType==c.ELEMENT_NODE and (tag is None or c.tagName==tag)]
def text(n,tag):
    a=children(n,tag)
    return '' if not a else ''.join(c.data for c in a[0].childNodes if c.nodeType in (c.TEXT_NODE,c.CDATA_SECTION_NODE))
def put(n,tag,value):
    a=children(n,tag)
    if not a:a=[n.ownerDocument.createElement(tag)];n.appendChild(a[0])
    for e in a:
        while e.firstChild:e.removeChild(e.firstChild)
        e.appendChild(n.ownerDocument.createTextNode(str(value)))
def code(n,tag,value):
    put(n,tag,value)
    for e in children(n,tag):
        while e.firstChild:e.removeChild(e.firstChild)
        e.appendChild(n.ownerDocument.createCDATASection(value))

def main():
    if OUT.exists() and '--actualizar' not in sys.argv:raise SystemExit('Preserve/review existing output before rebuilding: '+str(OUT))
    if (OUTPUT.with_suffix('.alp.autosave')).exists():raise SystemExit('The candidate has editor changes; preserve them before rebuilding')
    source=max([p for p in SOURCE_DIR.glob('Domitec_Main_3D.alp*') if p.suffix in ['.alp','.autosave']],key=lambda p:p.stat().st_mtime)
    d=D.parse(str(source));model=children(d.documentElement,'Model')[0]
    agents={text(a,'Name'):a for a in children(children(model,'ActiveObjectClasses')[0],'ActiveObjectClass')}
    mainA,plant,client,supplier,batch=[agents[n] for n in ['Main','DomitecPlant','Client','Supplier','Batch']]
    scene=lambda a:children(children(children(a,'Presentation')[0],'Level')[0],'Presentation')[0]
    ps,ms=scene(plant),scene(mainA)
    uid=3699500000000
    def fresh(n):
        nonlocal uid
        for e in [n]+list(n.getElementsByTagName('*')):
            if getattr(e,'tagName',None)=='Id':
                uid+=1
                while e.firstChild:e.removeChild(e.firstChild)
                e.appendChild(d.createTextNode(str(uid)))
    def base(n,name,x=0,y=0,mode='SHAPE_DRAW_2D'):
        nonlocal uid
        uid+=1
        for k,v in {'Id':uid,'Name':name,'X':x,'Y':y,'PublicFlag':'true','PresentationFlag':'true','ShowLabel':'false','DrawMode':mode,'EmbeddedIcon':'false'}.items():put(n,k,v)
        return n
    def variable(agent,name,typ,default,parameter=False):
        container=children(agent,'Variables')[0]
        template=next(v for v in children(container,'Variable') if v.getAttribute('Class')==('Parameter' if parameter else 'PlainVariable'))
        n=template.cloneNode(True);fresh(n);put(n,'Name',name);put(n,'PresentationFlag','false');put(n,'ShowLabel','false')
        prop=children(n,'Properties')[0];put(prop,'Type',typ)
        for tag in ['InitialValue','DefaultValue']:
            for q in children(prop,tag):prop.removeChild(q)
        q=d.createElement('DefaultValue' if parameter else 'InitialValue');q.setAttribute('Class','CodeValue');code(q,'Code',default);prop.appendChild(q);container.appendChild(n)
        return text(n,'Id')
    param_ids={}
    for name,typ,value in [('semillaReplica','int','1'),('numeroEscenario','int','-1'),('esComparacion','boolean','false'),('configuracionInicial','ConfiguracionDomitec','null')]:
        param_ids[name]=variable(mainA,name,typ,value,True)
    for name,value in [('uiMedia',9379),('uiDesvio',11162),('uiLead',30),('uiCobertura',5.5),('uiRate',667),('uiLatigo',1.5),('uiHoras',40),('uiMermaLav',3),('uiMermaLiq',5),('uiTiempo',1),('uiCapacidad',1),('uiWarmup',15)]:variable(mainA,name,'double',str(value))
    for name,value in [('uiReactores',4),('uiCola',20),('uiTanque',3)]:variable(mainA,name,'int',str(value))
    variable(mainA,'carpetaResultados','String','java.nio.file.Paths.get(System.getProperty("user.dir"),"resultados_domitec").toAbsolutePath().toString()')
    variable(batch,'indiceCRN','long','0') if any(v.getAttribute('Class')=='PlainVariable' for v in children(children(batch,'Variables')[0],'Variable')) else None
    if not any(text(v,'Name')=='indiceCRN' for v in children(children(batch,'Variables')[0],'Variable')):
        n=children(children(batch,'Variables')[0],'Variable')[0].cloneNode(True);fresh(n);n.setAttribute('Class','PlainVariable');put(n,'Name','indiceCRN');put(n,'PresentationFlag','false');put(n,'ShowLabel','false')
        prop=children(n,'Properties')[0];put(prop,'Type','long')
        for old in children(prop,'DefaultValue'):prop.removeChild(old)
        val=d.createElement('InitialValue');val.setAttribute('Class','CodeValue');code(val,'Code','0');prop.appendChild(val);children(batch,'Variables')[0].appendChild(n)
    for a in agents.values():
        for v in children(children(a,'Variables')[0],'Variable') if children(a,'Variables') else []:put(v,'PresentationFlag','false');put(v,'ShowLabel','false')
    additional=(ROOT/'tools/MainInterfaz.code.java.txt').read_text(encoding='utf8')
    additional=re.sub(r'^public (?:double uiMedia|double uiLatigo|int uiReactores|String carpetaResultados).*?;\n','',additional,flags=re.M)
    code(mainA,'AdditionalClassCode',additional)
    code(mainA,'StartupCode','iniciarInterfaz();')
    code(plant,'AdditionalClassCode',(ROOT/'tools/PlantaControl.code.java.txt').read_text(encoding='utf8'))

    # Deterministic demand keyed by replication, channel, product and week.
    event=children(children(client,'Events')[0])[0]
    code(event,'Action','''if (time() >= 100.0) return;
Main m=(Main)get_Main();
for(String nombre:ConfiguracionDomitec.PRODUCTOS){
    ProductType producto=ProductType.valueOf(nombre);
    double cantidad=m.demandaComun(clientName,producto);
    if(cantidad>0){m.demandaHistorica+=cantidad;m.demandaSemanalActual+=cantidad;send(new OrderMessage(producto,cantidad),m.domitecPlant);}
}''')
    code(children(supplier,'AgentProperties')[0],'OnReceive','''if(msg instanceof OrderMessage){
    OrderMessage orden=(OrderMessage)msg;
    Main m=(Main)get_Main();int p=ConfiguracionDomitec.indice(orden.product.name());
    create_DeliverOrder(m.cfg.leadDias[p]/7.0,WEEK,orden.product,orden.amount);
}''')
    blocks={text(b,'Name'):b for b in children(children(plant,'EmbeddedObjects')[0],'EmbeddedObject')}
    # Explicit entity types are essential when a Source factory is a function
    # call. AnyLogic cannot always infer its return type from additional code.
    for b in blocks.values():
        for generic in children(b,'GenericParameterSubstitute'):
            values=children(generic,'GenericParameterSubstituteValue')
            if not values:
                value=d.createElement('GenericParameterSubstituteValue');value.setAttribute('Class','CodeValue');generic.appendChild(value)
            else:value=values[0]
            code(value,'Code','Batch')
    def parameter(name,key,value):
        p=next(n for n in children(children(blocks[name],'Parameters')[0],'Parameter') if text(n,'Name')==key)
        for q in children(p,'Value'):p.removeChild(q)
        q=d.createElement('Value');q.setAttribute('Class','CodeValue');code(q,'Code',value);p.appendChild(q)
    def getparam(name,key):
        p=next(n for n in children(children(blocks[name],'Parameters')[0],'Parameter') if text(n,'Name')==key)
        v=children(p,'Value');return text(v[0],'Code') if v else ''
    parameter('sourceLavandina','newEntity','crearLote(ProductType.LAVANDINA)')
    parameter('sourceLiquidos','newEntity','crearLiquido()')
    parameter('sourceLiquidos','onExit',getparam('sourceLiquidos','onExit').replace('agent.tipo = tipoLiquidoRecibido;',''))
    for name,stage,values in [('delayDilucion',1,(50,70,90)),('delayQCLavandina',2,(10,15,25)),('delayReactoresLiquidos',3,(45,60,80)),('delayQCLiquidos',4,(15,20,35))]:
        parameter(name,'delayTime',f'tiempoProceso(agent,{stage},{values[0]},{values[1]},{values[2]})')
    for name in blocks:
        if name.startswith('delayEnvasado'):parameter(name,'delayTime','tiempoEnvasado(agent)')
    for name,lav in [('checkCalidadLavandina','true'),('checkCalidadLiquidos','false')]:
        parameter(name,'conditionIsProbabilistic','false');parameter(name,'condition',f'calidadAceptada(agent,{lav})')
    receive=text(children(plant,'AgentProperties')[0],'OnReceive')
    receive=receive.replace('despachoTotalAcumulado += dispatched;','despachoTotalAcumulado += dispatched;\n        controlador().registrarPedido(ps.product,order.amount,dispatched);')
    receive=receive.replace('sourceLiquidos.inject();','tiposPendientes.addLast(delivery.product);\n                sourceLiquidos.inject();')
    code(children(plant,'AgentProperties')[0],'OnReceive',receive)
    for name,prod in [('sinkTerminado','ProductType.LAVANDINA'),('sinkLiquidosTerminados','agent.tipo')]:
        action=getparam(name,'onEnter')
        action=action.replace('despachoTotalAcumulado += recovered;',f'despachoTotalAcumulado += recovered;\ncontrolador().registro.diferido(ConfiguracionDomitec.indice({prod}.name()),time(),recovered);')
        action+=f'\ncontrolador().registrarProduccion({prod},agent.cajasEquivalentes);'
        parameter(name,'onEnter',action)
    weekly=next(e for e in children(children(plant,'Events')[0]) if text(e,'Name')=='planificacionSemanal')
    action=text(weekly,'Action')
    start=action.index('double semanasCobertura =');end=action.index('double targetStock',start)
    action=action[:start]+'double semanasCobertura = controlador().cfg.cobertura[ConfiguracionDomitec.indice(ps.product.name())];\n    '+action[end:]
    action=re.sub(r'// --- ACTUALIZACION EN TIEMPO REAL DEL DASHBOARD INTERACTIVO EN MAIN ---.*?// ----------------------------------------------------------------------','',action,flags=re.S)
    action=action.replace('m.ordenesSemanalActual = totalOrdenesSemana;','m.ordenesSemanalActual = totalOrdenesSemana;\nif(time()<100)m.ordenesPorSemana[(int)Math.floor(time())]+=totalOrdenesSemana;')
    code(weekly,'Action',action)
    # Observe complete weeks just before the next week's demand. Exactly 100 samples.
    sampler=event.cloneNode(True);fresh(sampler);put(sampler,'Name','observarSemana');code(sampler,'Action','observarSemana();')
    prop=children(sampler,'Properties')[0];code(children(prop,'OccurrenceTime')[0],'Code','0.9999')
    events=children(mainA,'Events')
    if not events:e=d.createElement('Events');mainA.appendChild(e)
    else:e=events[0]
    e.appendChild(sampler)

    # Plant is embedded in Main for both views; leave geometry in its own agent.
    original_camera=next(n for n in children(ps,'Camera3D'))
    window_template=next(n for n in children(ps,'Control') if n.getAttribute('Type')=='Window3D')
    for n in list(children(ps)):
        if n.tagName in ['Control','Camera3D'] or text(n,'Name') in ['amb_barra_vista','amb_titulo_vista']:
            ps.removeChild(n)
    for n in ps.getElementsByTagName('*'):
        if children(n,'EmbeddedIcon'):put(n,'EmbeddedIcon','true')
    for n in ps.getElementsByTagName('Figure3D'):put(n,'DrawMode','SHAPE_DRAW_3D');put(n,'EmbeddedIcon','true')
    # 2D lot markers follow the very same passive lot state as the 3D containers.
    rect_template=next(n for n in children(ps,'Rectangle'))
    for f in list(ps.getElementsByTagName('Figure3D')):
        name=text(f,'Name')
        if not name.startswith('completa_') or not any(t in name for t in ['_envase_','_caja_','_salida_']):continue
        n=rect_template.cloneNode(True);fresh(n)
        for tag in ['XCode','YCode','WidthCode','VisibleCode','FillColorCode']:
            for old in children(n,tag):n.removeChild(old)
        for k,v in {'Name':'plano_'+name,'X':850,'Y':700,'Width':7,'Height':7,'Z':1,'ZHeight':0,'DrawMode':'SHAPE_DRAW_2D','EmbeddedIcon':'true','FillColor':-26624 if '_envase_' not in name else -15238159,'LineWidth':0}.items():put(n,k,v)
        for tag in ['XCode','YCode','VisibleCode']:code(n,tag,text(f,tag))
        ps.appendChild(n)

    # Author a single tidy Main canvas: fixed header, three settings blocks, four bodies.
    plots=[n.cloneNode(True) for n in children(ms,'TimePlot')]
    rect=next(n for n in children(ps,'Rectangle')).cloneNode(True)
    txt=next(n for n in children(ps,'Text')).cloneNode(True)
    control_template=next(n.cloneNode(True) for n in ms.getElementsByTagName('Control') if n.getAttribute('Type')=='Button')
    check_template=next(n.cloneNode(True) for n in ms.getElementsByTagName('Control') if n.getAttribute('Type')=='CheckBox')
    while ms.firstChild:ms.removeChild(ms.firstChild)
    def group(name,visible):
        n=base(d.createElement('Group'),name);put(n,'Z',0);put(n,'Rotation',0);code(n,'VisibleCode',visible)
        p=d.createElement('Presentation');n.appendChild(p);ms.appendChild(n);return p
    def panel(parent,name,x,y,w,h,color,line=None):
        n=rect.cloneNode(True);fresh(n)
        for c in list(children(n)):
            if c.tagName.endswith('Code'):n.removeChild(c)
        for k,v in {'Name':name,'X':x,'Y':y,'Width':w,'Height':h,'Z':0,'ZHeight':0,'DrawMode':'SHAPE_DRAW_2D','EmbeddedIcon':'false','FillColor':color,'LineColor':line or color,'LineWidth':1 if line else 0}.items():put(n,k,v)
        parent.appendChild(n);return n
    def label(parent,name,x,y,value,size=12,color=-14340540,expr=None):
        n=txt.cloneNode(True);fresh(n)
        for c in list(children(n)):
            if c.tagName.endswith('Code'):n.removeChild(c)
        for k,v in {'Name':name,'X':x,'Y':y,'Z':0,'DrawMode':'SHAPE_DRAW_2D','EmbeddedIcon':'false','Color':color,'Text':value}.items():put(n,k,v)
        font=children(n,'Font')[0];put(font,'Name','SansSerif');put(font,'Size',size);put(font,'Style',0)
        if expr:code(n,'TextCode',expr.replace(r'\\n',r'\n'))
        parent.appendChild(n);return n
    def button(parent,name,x,y,w,value,action,selected=None):
        n=control_template.cloneNode(True);fresh(n);put(n,'Name',name);put(n,'X',x);put(n,'Y',y);put(n,'DrawMode','SHAPE_DRAW_2D')
        b=children(n,'BasicProperties')[0];b.setAttribute('Width',str(w));b.setAttribute('Height','30');code(b,'ActionCode',action)
        ex=children(n,'ExtendedProperties')[0];put(ex,'LabelText',value)
        parent.appendChild(n);return n
    def edit(parent,name,x,y,w,link):
        n=check_template.cloneNode(True);fresh(n);n.setAttribute('Type','EditBox');put(n,'Name',name);put(n,'X',x);put(n,'Y',y);put(n,'DrawMode','SHAPE_DRAW_2D')
        b=children(n,'BasicProperties')[0];b.setAttribute('Width',str(w));b.setAttribute('Height','28');put(b,'FillColor',-1);put(b,'TextColor',-14340540)
        ex=children(n,'ExtendedProperties')[0];put(ex,'Link',link)
        for old in children(ex,'LabelText'):ex.removeChild(old)
        parent.appendChild(n);return n
    dark=-15193551;teal=-14381747;bg=-658189;border=-1906964;muted=-9603453
    panel(ms,'fondoUI',0,0,1280,1000,bg)
    panel(ms,'cabeceraUI',0,0,1280,64,dark)
    label(ms,'marcaUI',24,40,'DOMITEC | SIMULACION DE PLANTA',19,-1)
    for i,(name,title) in enumerate([('vista2D','Vista 2D'),('vista3D','Vista 3D'),('estadisticas','Estadisticas'),('logica','Logica')]):
        button(ms,name,620+i*158,17,144,title,f'mostrarVista({i});')
        bar=panel(ms,'tabActiva'+str(i),620+i*158,55,144,4,-11546643);code(bar,'VisibleCode',f'vistaActiva == {i}')
    for name,x,w in [('vista',24,360),('escenarios',400,430),('parametros',846,410)]:panel(ms,'bloque_'+name,x,77,w,106,-1,border)
    label(ms,'tituloVista',40,101,'VISTA EN VIVO',11,teal)
    label(ms,'tiempoUI',40,126,'Tiempo',13,expr='"Semana " + String.format(java.util.Locale.ROOT,"%.2f",time()) + " / 100  |  Semilla " + semillaReplica')
    checkbox=check_template.cloneNode(True);fresh(checkbox);put(checkbox,'Name','operariosUI');put(checkbox,'X',40);put(checkbox,'Y',144);put(children(checkbox,'ExtendedProperties')[0],'Link','domitecPlant.animarOperarios');put(children(checkbox,'ExtendedProperties')[0],'LabelText','Recorridos de operarios');ms.appendChild(checkbox)
    label(ms,'tituloEscenarios',416,101,'ESCENARIO / EXPERIMENTO',11,teal)
    for i,title in enumerate(['0 - As-Is','1 - Sin panico','2 - Integral']):button(ms,'escenarioUI'+str(i),416+i*132,111,124,title,f'elegirEscenario({i});')
    label(ms,'escenarioActivoUI',416,165,'Escenario',11,muted,expr='escenarioTexto() + " | alfa=" + cfg.factLatigo + " | horas=" + cfg.horas')
    label(ms,'tituloParametros',862,101,'PARAMETROS EN TIEMPO REAL',11,teal)
    label(ms,'perfilActivoUI',862,124,'Perfil',12,expr='perfilTexto()')
    button(ms,'editarLogicaUI',862,138,170,'Editar logica','mostrarVista(3);')
    label(ms,'warmupHeader',1046,157,'Warm-up',11,muted,expr='"Warm-up: " + cfg.calentamiento + " sem"')
    for i in range(4):
        # Body groups share coordinates, so changing tabs never leaves Main.
        g=group('cuerpoVista'+str(i),f'vistaActiva == {i}')
        panel(g,'fondoCuerpo'+str(i),24,200,1232,698,-1,border)
        if i==0:
            label(g,'rotuloPlano',40,223,'PLANO 2D | Sector Parque y Sector Vicentin',13,teal)
            panel(g,'resumenPlano',938,242,296,398,bg,border)
            label(g,'tituloResumenPlano',956,271,'ESTADO DE LA PLANTA',13,teal)
            label(g,'estadoPlano',956,307,'Estado',13,expr='"Stock: " + numero(stockActual()) + " cajas\\n\\nBacklog: " + numero(backlogActual()) + " cajas\\n\\nWIP: " + numero(wipActual()) + " cajas\\n\\nProduccion: " + numero(registro.produccionTotal(cfg.calentamiento)) + " cajas\\n\\nServicio: " + String.format(java.util.Locale.ROOT,"%.2f%%",100*registro.fillRate(cfg.calentamiento))')
            label(g,'notaPlano',956,691,'Marcadores = lotes reales\nColas y stock se actualizan\ncon el proceso.',11,muted)
        elif i==1:
            n=window_template.cloneNode(True);fresh(n)
            for k,v in {'Name':'ventanaPlanta3D','X':25,'Y':201,'Width':1230,'Height':696,'MakeDefaultViewArea':'false','Camera':'camaraMain','FarClippingDistance':4000}.items():put(n,k,v)
            g.appendChild(n)
        elif i==2:
            label(g,'tituloStats',40,231,'ESTADISTICAS | Ventana posterior al calentamiento',14,teal)
            button(g,'estudioUI',842,211,230,'Ejecutar 100 ternas (300)','ejecutarComparacion();')
            button(g,'detenerEstudioUI',1084,211,150,'Detener estudio','cancelarComparacion();')
            for n,(x,y,w,h) in zip(plots,[(40,267,580,256),(660,267,580,256),(40,570,790,276)]):
                for k,v in {'X':x,'Y':y,'Width':w,'Height':h,'DrawMode':'SHAPE_DRAW_2D'}.items():put(n,k,v)
                chart=children(n,'ChartArea')[0];put(chart,'Width',w-78);put(chart,'Height',h-85)
                g.appendChild(n)
            label(g,'estadoEstudioUI',40,551,'Estado',11,muted,expr='SesionEstudio.estado + " | " + SesionEstudio.progreso + "/300"')
            panel(g,'panelPareados',852,570,382,306,bg,border)
            for j,(title,metric) in enumerate([('Servicio',0),('Backlog',1),('Latigo',2)]):button(g,'metricaIC'+str(j),866+j*118,581,110,title,f'metricaIC={metric};')
            label(g,'tablaPareadosUI',868,641,'IC pareados',11,expr='tablaIC()')
            label(g,'notaEstacionariaUI',40,877,'Calentamiento no implica estacionariedad: revisar las series semanales y su tendencia.',11,muted)
        else:
            for name,x,w in [('demanda',40,370),('inventario',430,380),('proceso',830,404)]:panel(g,'card_'+name,x,222,w,621,bg,border)
            label(g,'tituloDemandaUI',56,249,'DEMANDA | Media y desvio',14,teal)
            for c,title in enumerate(['Maxiconsumo','Grandes cli.','Red propia']):button(g,'canalUI'+str(c),56+c*114,265,106,title,f'seleccionarPerfil({c},perfilProducto);')
            for p,title in enumerate(['Lavandina','Desinfectante','Lavavajilla','Lavarropa','Suavizante','Detergente']):button(g,'productoUI'+str(p),56+(p%2)*168,310+(p//2)*39,160,title,f'seleccionarPerfil(perfilCanal,{p});')
            label(g,'perfilFormUI',56,448,'Perfil',11,muted,expr='perfilTexto()')
            label(g,'mediaLabel',56,480,'Media (cajas / semana)',11);edit(g,'campoMedia',56,488,150,'uiMedia')
            label(g,'sdLabel',230,480,'Desvio estandar',11);edit(g,'campoDesvio',230,488,150,'uiDesvio')
            label(g,'varianzaLabel',56,547,'Varianza',11,muted,expr='"Varianza = " + numero(uiDesvio*uiDesvio)')
            button(g,'aplicarDemandaUI',56,565,320,'Aplicar demanda al perfil','guardarDemanda();')
            label(g,'notaDemandaUI',56,626,'Normal truncada en cero,\nredondeada a cajas enteras.\n\nEl sorteo depende de semilla, canal,\nproducto y semana; no del orden\nde los eventos de produccion.',12,muted)
            label(g,'tituloInventarioUI',446,249,'INVENTARIO Y OPERACION',14,teal)
            for j,(lab,name,link) in enumerate([('Factor latigo (alfa)','campoLatigo','uiLatigo'),('Horas operativas / semana','campoHoras','uiHoras'),('Lead time (dias, producto)','campoLead','uiLead'),('Cobertura (semanas, producto)','campoCobertura','uiCobertura'),('Envasado (cajas/h, producto)','campoRate','uiRate'),('Multiplicador de capacidad','campoCapacidad','uiCapacidad')]):
                label(g,name+'Label',446,285+j*78,lab,11);edit(g,name,446,294+j*78,340,link)
            label(g,'tituloProcesoUI',846,249,'PROCESO Y MEDICION',14,teal)
            for j,(lab,name,link) in enumerate([('Rechazo lavandina (%)','campoMermaLav','uiMermaLav'),('Rechazo liquidos (%)','campoMermaLiq','uiMermaLiq'),('Factor de tiempos de proceso','campoTiempo','uiTiempo'),('Calentamiento (0 a <100 semanas)','campoWarmup','uiWarmup'),('Reactores en paralelo','campoReactores','uiReactores'),('Capacidad cola / tanques (lotes)','campoCola','uiCola')]):
                label(g,name+'Label',846,285+j*72,lab,11);edit(g,name,846,294+j*72,340,link)
            label(g,'tanqueLabel',846,730,'Capacidad de cada tanque',11);edit(g,'campoTanque',846,738,340,'uiTanque')
            button(g,'aplicarPlantaUI',446,800,740,'Aplicar parametros de planta y medicion','guardarPlanta();')
            label(g,'rutaCSVLabel',40,868,'Carpeta de resultados CSV',10,muted);edit(g,'campoCarpeta',240,850,994,'carpetaResultados')
    camera=original_camera.cloneNode(True);fresh(camera);put(camera,'Name','camaraMain');ms.appendChild(camera)
    # Persistent footer: all tabs see the same live KPIs.
    footer=[('Fill Rate','time()<cfg.calentamiento ? "Calentando" : String.format(java.util.Locale.ROOT,"%.2f%%",100*registro.fillRate(cfg.calentamiento))'),('Backlog','numero(backlogActual())'),('Stock','numero(stockActual())'),('WIP','numero(wipActual())'),('Produccion','numero(registro.produccionTotal(cfg.calentamiento))'),('Razon BW','String.format(java.util.Locale.ROOT,"%.3f",registro.bw(cfg.calentamiento))')]
    for i,(title,expr) in enumerate(footer):
        panel(ms,'kpiCard'+str(i),24+i*208,910,192,65,-1,border);label(ms,'kpiTitulo'+str(i),36+i*208,930,title,10,muted);label(ms,'kpiValor'+str(i),36+i*208,959,'0',19,teal,expr)
    label(ms,'mensajeUItexto',24,994,'Mensaje',11,muted,expr='mensajeUI')

    # Add the plain Java helpers, then configure seed/scenario parameters on each experiment.
    java_classes=children(model,'JavaClasses')[0]
    for name in ['ComparacionEscenarios','ConfiguracionDomitec','RegistroCorrida','SesionEstudio','EstudioPareado']:
        n=d.createElement('JavaClass');uid+=1;put(n,'Id',uid);put(n,'Name',name);code(n,'Text',(ROOT/'tools'/f'{name}.java').read_text(encoding='utf8'));java_classes.appendChild(n)
    experiments=children(model,'Experiments')[0]
    pv=next(n for n in children(experiments) if n.tagName=='ParamVariationExperiment').cloneNode(True);fresh(pv);put(pv,'Name','Comparacion_100x3');put(pv,'NumberOfRuns',100)
    reps=children(pv,'ReplicationsProperties')[0];put(reps,'UseReplication','true');put(reps,'FixedReplicationsNumber','true');put(reps,'ReplicationPerIteration',3)
    put(pv,'CustomGeneratorCode','new Random(getCurrentIteration())');put(pv,'AllowParallelEvaluations','false')
    code(pv,'AdditionalClassCode','public EstudioPareado estudio=new EstudioPareado();')
    def freeform(exp,name,expr):
        target=next((n for n in children(exp,'FreeformParamValue') if text(n,'Id')==param_ids[name]),None)
        if target is None:target=d.createElement('FreeformParamValue');put(target,'Id',param_ids[name]);exp.appendChild(target)
        q=d.createElement('Expression');q.setAttribute('Class','CodeValue');code(q,'Code',expr);target.appendChild(q)
    for k,v in {'semillaReplica':'getCurrentIteration()','numeroEscenario':'getCurrentReplication()-1','esComparacion':'true','configuracionInicial':'SesionEstudio.configuracionEnCurso == null ? new ConfiguracionDomitec() : SesionEstudio.configuracionEnCurso.copiarDeep()'}.items():freeform(pv,k,v)
    # Scenario parameters are propagated explicitly before any model startup.
    for n in children(pv,'FreeformParamValue'):
        if text(n,'Id') in [text(v,'Id') for v in children(children(mainA,'Variables')[0],'Variable') if text(v,'Name') in ['factorLatigoMain','escalaTurnoMain']]:
            for q in children(n,'Expression'):n.removeChild(q)
    code(pv,'AfterSimulationRunCode','''if(root.semillaReplica==1 && root.numeroEscenario==0)estudio=new EstudioPareado();
if(root.registro.numeroSemanas()!=100 || root.registro.numeroEntradas()!=1800)throw new IllegalStateException("Corrida incompleta: se requieren 100 semanas y 1800 entradas de demanda");
estudio.agregar(root.resultadoFinal(root.numeroEscenario),root.registro.firmaDemanda(),root.registro.seriesCsv(root.semillaReplica,root.numeroEscenario),root.cfg.calentamiento,root.cfg,SesionEstudio.carpetaEnCurso);''')
    experiments.appendChild(pv)
    for e in children(experiments):
        put(e,'MaximumMemory',1024)
        tp=children(e,'ModelTimeProperties')[0];put(tp,'InitialTime',0);put(tp,'FinalTime',100)
        if e.tagName=='ParamVariationExperiment' and text(e,'Name')!='Comparacion_100x3':
            sc=['ParametersVariation','ParametersVariation1','ParametersVariation2'].index(text(e,'Name'))
            put(e,'NumberOfRuns',1);put(e,'AllowParallelEvaluations','false');put(e,'CustomGeneratorCode','new Random(getCurrentReplication())');put(e,'RandomNumberGenerationType','customGenerator')
            put(children(e,'ReplicationsProperties')[0],'ReplicationPerIteration',100)
            for k,v in {'semillaReplica':'getCurrentReplication()','numeroEscenario':str(sc),'esComparacion':'true'}.items():freeform(e,k,v)
            code(e,'AfterSimulationRunCode','ComparacionEscenarios.Resultado r=root.resultadoFinal(root.numeroEscenario); traceln("seed="+r.seed+",escenario="+r.escenario+",firma_demanda="+root.registro.firmaDemanda()+",fillRate="+r.fillRate+",backlog="+r.backlog+",bw="+r.bw);')
        elif e.tagName=='SimulationExperiment':
            put(e,'RandomNumberGenerationType','fixedSeed');put(e,'SeedValue',1)
    put(pv,'RandomNumberGenerationType','customGenerator')
    frame=children(model,'Frame')[0];put(frame,'Width',1280);put(frame,'Height',1010)
    put(children(model,'Database')[0],'Logging','false')
    from ajustar_presentacion import ajustar
    ajustar(d)
    put(model,'Name','Domitec_Interactivo');put(model,'JavaPackageName','domitec_interactivo')
    mapping={}
    for n in d.getElementsByTagName('Id'):
        val=''.join(c.data for c in n.childNodes if c.nodeType in [c.TEXT_NODE,c.CDATA_SECTION_NODE]).strip()
        if val not in mapping:mapping[val]=str(3699000000000+len(mapping)+1)
    for n in d.getElementsByTagName('*'):
        if n.tagName=='PackageName' and text(n.parentNode,'PackageName')=='domitec_main_3d':put(n.parentNode,'PackageName','domitec_interactivo')
        for c in n.childNodes:
            if c.nodeType in [c.TEXT_NODE,c.CDATA_SECTION_NODE] and c.data.strip() in mapping:c.data=mapping[c.data.strip()]
        for i in range(n.attributes.length):
            a=n.attributes.item(i)
            if a.value in mapping:a.value=mapping[a.value]
    OUT.mkdir(exist_ok=True);shutil.copytree(SOURCE_DIR/'3d',OUT/'3d',dirs_exist_ok=True)
    # A separate database avoids interfering with the project open in AnyLogic.
    for path in subprocess.check_output(['git','ls-tree','-r','--name-only','main'],cwd=ROOT).decode().splitlines():
        if path.startswith('database/') and not path.endswith(('.lck','.tmp')):
            target=OUT/path;target.parent.mkdir(exist_ok=True,parents=True)
            if not target.exists():target.write_bytes(subprocess.check_output(['git','show','main:'+path],cwd=ROOT))
    OUTPUT.write_bytes(d.toxml(encoding='UTF-8'))
    (OUT/'cambios_interfaz.json').write_text(json.dumps({'source':str(source),'model_time':'Week','horizon':100,'replicas_per_scenario':100,'batch_order':'seed1:[0,1,2], seed2:[0,1,2], ..., seed100:[0,1,2]','warmup_default':15,'new_weekly_observation_time':'.9999 + k weeks','sampling':'keyed CRN by replication/channel/product/week and lot/stage','ui_tabs':['2D','3D','Estadisticas','Logica']},indent=2),encoding='utf8')
    print(OUTPUT)

if __name__=='__main__':main()
