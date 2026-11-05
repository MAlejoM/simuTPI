"""Refine the existing UI, preserving business logic and backing up editor files."""
from pathlib import Path
from xml.dom import minidom as D
import re, shutil, tempfile
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

def main():
    backup=Path(tempfile.mkdtemp(prefix='domitec-antes-orden-visual-'))
    for p in (ROOT/'domitec_interactivo').glob('Domitec_Interactivo.alp*'):
        if p.suffix not in ['.alp','.autosave']:continue
        shutil.copy2(p,backup/p.name)
        d=D.parse(str(p));ajustar(d);p.write_bytes(d.toxml(encoding='UTF-8'))
        print('Updated',p.name)
    print('Backup:',backup)

if __name__=='__main__':main()
