"""Add readable plant guides and isolate the old 2D drawing from the 3D scene."""
from pathlib import Path
import json
from crear_interfaz import children, text, put, code

ROOT=Path(__file__).resolve().parents[1]

def documentar(d):
    model=children(d.documentElement,'Model')[0]
    agents={text(a,'Name'):a for a in children(children(model,'ActiveObjectClasses')[0],'ActiveObjectClass')}
    plant,main=agents['DomitecPlant'],agents['Main']
    scene=lambda a:children(children(children(a,'Presentation')[0],'Level')[0],'Presentation')[0]
    ps,ms=scene(plant),scene(main)
    sectors=json.loads((ROOT/'tools/sectores_planta.json').read_text(encoding='utf8'))
    uid=max(int(n.firstChild.data) for n in d.getElementsByTagName('Id') if n.firstChild and n.firstChild.data.isdigit())
    def fresh(n):
        nonlocal uid
        for p in [n]+list(n.getElementsByTagName('*')):
            if p.tagName=='Id':
                uid+=1
                while p.firstChild:p.removeChild(p.firstChild)
                p.appendChild(d.createTextNode(str(uid)))
    def named(parent,name):return next(n for n in parent.getElementsByTagName('*') if text(n,'Name')==name)
    rect=named(ms,'fondoUI').cloneNode(True);txt=named(ms,'mediaLabel').cloneNode(True)
    btn=named(ms,'editarLogicaUI').cloneNode(True)
    def group(parent,name,x=0,y=0,mode='SHAPE_DRAW_2D',visible=None):
        n=d.createElement('Group');put(n,'Id',0);fresh(n)
        for k,v in {'Name':name,'X':x,'Y':y,'Z':0,'Rotation':0,'DrawMode':mode,'EmbeddedIcon':'false','PublicFlag':'false','PresentationFlag':'true','ShowLabel':'false'}.items():put(n,k,v)
        if visible is not None:code(n,'VisibleCode',visible)
        p=d.createElement('Presentation');n.appendChild(p);parent.appendChild(n);return n,p
    def clean(n):
        for c in list(children(n)):
            if c.tagName.endswith('Code'):n.removeChild(c)
    def panel(parent,name,x,y,w,h,color,mode='SHAPE_DRAW_2D',line=None):
        n=rect.cloneNode(True);fresh(n);clean(n)
        for k,v in {'Name':name,'X':x,'Y':y,'Z':1.2 if mode=='SHAPE_DRAW_3D' else 0,'Width':w,'Height':h,'ZHeight':.2 if mode=='SHAPE_DRAW_3D' else 0,'FillColor':color,'LineColor':color if line is None else line,'LineWidth':0 if line is None else 1,'DrawMode':mode,'PublicFlag':'true' if mode=='SHAPE_DRAW_3D' else 'false','EmbeddedIcon':'false','ShowLabel':'false'}.items():put(n,k,v)
        parent.appendChild(n);return n
    def label(parent,name,x,y,value,size=13,color=-14340540,expr=None,mode='SHAPE_DRAW_2D'):
        n=txt.cloneNode(True);fresh(n);clean(n)
        for k,v in {'Name':name,'X':x,'Y':y,'Z':1.6 if mode=='SHAPE_DRAW_3D' else 0,'Text':value,'Color':color,'DrawMode':mode,'PublicFlag':'true' if mode=='SHAPE_DRAW_3D' else 'false','EmbeddedIcon':'false','ShowLabel':'false'}.items():put(n,k,v)
        put(children(n,'Font')[0],'Size',size)
        if expr:code(n,'TextCode',expr)
        parent.appendChild(n);return n
    def button(parent,name,x,y,w,value,action):
        n=btn.cloneNode(True);fresh(n)
        for k,v in {'Name':name,'X':x,'Y':y,'ShowLabel':'false'}.items():put(n,k,v)
        bp=children(n,'BasicProperties')[0];bp.setAttribute('Width',str(w));bp.setAttribute('Height','27');code(bp,'ActionCode',action)
        put(children(n,'ExtendedProperties')[0],'LabelText',value);parent.appendChild(n)
    # Remove only guides authored by this script when updating an existing model.
    for n in list(children(ps)):
        if text(n,'Name').startswith('guia_'):ps.removeChild(n)
    body3=children(named(ms,'cuerpoVista1'),'Presentation')[0]
    for n in list(children(body3)):
        if text(n,'Name').startswith('guia3D_'):body3.removeChild(n)
    # All logic stays connected, in the same relative arrangement, to the right.
    for tag in ['Variables','Ports','Events','Connectors','ContainerLinks','EmbeddedObjects','AnalysisData']:
        for container in children(plant,tag):
            for n in children(container):
                put(n,'PresentationFlag','false');put(n,'ShowLabel','false')
                if children(n,'X') and float(text(n,'X'))<2000:put(n,'X',float(text(n,'X'))+2000)
    legacy=next((n for n in children(ps,'Group') if text(n,'Name')=='compatibilidad2D'),None)
    if legacy is None:legacy,lp=group(ps,'compatibilidad2D',2000,3000,visible='false')
    else:lp=children(legacy,'Presentation')[0]
    for n in list(children(ps)):
        if n is legacy:continue
        if (n.tagName=='Text' and text(n,'DrawMode')!='SHAPE_DRAW_3D') or (n.tagName in ['Rectangle','Group'] and text(n,'DrawMode')=='SHAPE_DRAW_2D'):
            ps.removeChild(n);lp.appendChild(n)
    # Each marker and camera target derive from the same physical sector bounds.
    for i,s in enumerate(sectors):
        ax,ay,w,h=s['area'];x,y=ax+8,ay+8
        post=panel(ps,f'guia_poste_{i}',x+24,y+20,2,2,-14340540,'SHAPE_DRAW_3D');put(post,'Z',1);put(post,'ZHeight',109)
        plaque=panel(ps,f'guia_marca_{i}',x,y,50,42,-14381747,'SHAPE_DRAW_3D');put(plaque,'Z',110)
        number=label(ps,f'guia_numero_{i}',x+14,y+5,str(i+1),30,-1,mode='SHAPE_DRAW_3D');put(number,'Z',111)
        outline=panel(ps,f'guia_limite_{i}',ax,ay,w,h,-14381747,'SHAPE_DRAW_3D')
        put(outline,'FillColor','');put(outline,'LineColor',-11546643);put(outline,'LineWidth',4);put(outline,'Z',1);put(outline,'ZHeight',0)
        code(outline,'VisibleCode',f'controlador().sector3DActivo=={i}')
    # The agent's own 2D view is a complete plan, in a separate editor area.
    # Its coordinates do not overlap the 3D geometry or the process logic.
    _,local_plan=group(ps,'guia_plano2D',-1400,0)
    from plano_2d import crear_plano
    def plant_label(parent,name,x,y,value,size=12,color=-14340540,expr=None):
        if expr:
            for method in ['lotesEtapa','stockProducto','backlogProducto','numero']:
                expr=expr.replace(method+'(', 'controlador().'+method+'(')
            expr=expr.replace('cfg.','controlador().cfg.')
        return label(parent,name,x,y,value,size,color,expr)
    def plant_panel(parent,name,x,y,w,h,color,line=None):return panel(parent,name,x,y,w,h,color,line=line)
    crear_plano(local_plan,plant_panel,plant_label)
    label(local_plan,'guia_plano_titulo',40,35,'DOMITEC | PLANO DE LA PLANTA',24,-14381747)
    label(local_plan,'guia_plano_uso',40,80,'El mismo plano esta disponible en Main > Vista 2D. Para recorrer los modelos, usa Main > Vista 3D.',15)
    label(local_plan,'guia_plano_nota',40,125,'Parque: lavandina. Vicentin: cinco liquidos. Lotes, existencias y pedidos pendientes se actualizan en vivo.',14)
    origin=children(plant,'ClientAreaTopLeft')
    if not origin:origin=[d.createElement('ClientAreaTopLeft')];plant.appendChild(origin[0])
    put(origin[0],'X',-1400);put(origin[0],'Y',0)
    label(ps,'guia_editor_escena',350,130,'ESCENA 3D | Usar Main > Vista 3D',20,-14381747)
    # Main's 3D tab always has a legible guide, independent of camera orientation.
    window=named(ms,'ventanaPlanta3D');put(window,'Width',910)
    put(named(ms,'tituloPlanta3D'),'Text','PLANTA 3D | Perspectiva general')
    panel(body3,'guia3D_panel',955,244,280,653,-1)
    label(body3,'guia3D_titulo',970,259,'GUIA DE LA PLANTA',15,-14381747)
    for i,s in enumerate(sectors):
        button(body3,f'guia3D_sector_{i}',970,291+i*31,248,f'{i+1}. '+s['nombre'],f'sector3DActivo={i};')
        bar=panel(body3,f'guia3D_activo_{i}',962,291+i*31,4,27,-11546643)
        code(bar,'VisibleCode',f'sector3DActivo=={i}')
    label(body3,'guia3D_seleccion',970,587,'Sector',14,-14381747,expr='nombreSector3D()')
    label(body3,'guia3D_descripcion',970,618,'Descripción',13,expr='descripcionSector3D()')
    label(body3,'guia3D_nota',970,747,'El sector seleccionado se marca\ncon un contorno en el piso.\n\nCada lote representa 1.000 cajas.',12,-9603453)
    button(body3,'guia3D_enfocar',970,851,248,'Acercar al sector','enfocarSector3D();')
    java_strings=lambda values:'new String[]{'+','.join(json.dumps(v,ensure_ascii=False) for v in values)+'}'
    names=java_strings([str(i+1)+'. '+s['nombre'] for i,s in enumerate(sectors)])
    descriptions=java_strings([s['descripcion'] for s in sectors])
    centers='new double[][]{'+','.join('{'+str(s['area'][0]+s['area'][2]/2)+','+str(s['area'][1]+s['area'][3]/2)+'}' for s in sectors)+'}'
    extra=f'''\n// GUIA_PLANTA: presentation state only; it never changes production.
public int sector3DActivo=0;
public String nombreSector3D(){{return ({names})[sector3DActivo];}}
public String descripcionSector3D(){{return ({descriptions})[sector3DActivo];}}
public void enfocarSector3D(){{
    double[] c=({centers})[sector3DActivo];
    ventanaPlanta3D.setCamera(new com.anylogic.engine.presentation.Camera3D(c[0],c[1],600,Math.PI/2,0),false,0L);
}}
'''
    code(main,'AdditionalClassCode',text(main,'AdditionalClassCode')+extra)
