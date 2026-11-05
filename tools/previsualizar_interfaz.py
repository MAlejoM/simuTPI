"""Render XML layout previews for spacing checks, not a native AnyLogic capture."""
from pathlib import Path
import re, xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tools/_workspace_visual_qa'
FONT=Path('C:/Windows/Fonts/arial.ttf')

def color(value):
    value=int(value or -1)&0xffffff
    return ((value>>16)&255,(value>>8)&255,value&255)

def render(tab):
    tree=E.parse(ROOT/'domitec_interactivo/Domitec_Interactivo.alp')
    main=next(a for a in tree.findall('Model/ActiveObjectClasses/ActiveObjectClass') if a.findtext('Name')=='Main')
    scene=main.find('Presentation/Level/Presentation')
    im=Image.new('RGB',(1280,1010),'white');draw=ImageDraw.Draw(im)
    controls=[];texts=[]
    def visit(scene):
        for n in scene:
            name=n.findtext('Name','');x=float(n.findtext('X','0'));y=float(n.findtext('Y','0'))
            if n.tag=='Group':
                if name=='cuerpoVista'+str(tab):visit(n.find('Presentation'))
            elif n.tag=='Rectangle':
                if name.startswith('tabActiva') and name!='tabActiva'+str(tab):continue
                w=float(n.findtext('Width','0'));h=float(n.findtext('Height','0'))
                draw.rectangle((x,y,x+w,y+h),fill=color(n.findtext('FillColor')),outline=color(n.findtext('LineColor')))
            elif n.tag=='Text':
                value=n.findtext('Text','');expr=n.findtext('TextCode','')
                if expr:
                    if name.startswith('planoLote'):value='Lotes: 0'
                    elif name.startswith('planoStock'):value='Stock: 146000 cajas'
                    elif name.startswith('planoBacklog'):value='Backlog: 0 cajas'
                    elif name=='perfilFormUI' or name=='perfilActivoUI':value='Maxiconsumo / Lavandina'
                    elif name=='tiempoUI':value='Semana 4.32 / 100 | Semilla 1'
                    elif name=='escenarioActivoUI':value='0 - As-Is | alfa=1.5 | horas=40.0'
                    elif name=='warmupHeader':value='Warm-up: 15.0 sem'
                    elif name=='varianzaLabel':value='Varianza = 124.590.944'
                    elif name.startswith('kpiValor'):value='0' if name!='kpiValor0' else 'Calentando'
                font=ImageFont.truetype(str(FONT),int(n.findtext('Font/Size','12')))
                draw.multiline_text((x,y),value,font=font,fill=color(n.findtext('Color')),spacing=2)
                if name.endswith('Label') or name in ['mediaLabel','sdLabel','tanqueLabel']:
                    texts.append((name,draw.multiline_textbbox((x,y),value,font=font,spacing=2)))
            elif n.tag=='Control':
                b=n.find('BasicProperties');w=float(b.get('Width','100'));h=float(b.get('Height','28'))
                edit=n.get('Type')=='EditBox';check=n.get('Type')=='CheckBox'
                if check:
                    draw.rectangle((x,y,x+14,y+14),outline='#555555');w=14
                else:draw.rectangle((x,y,x+w,y+h),fill='white' if edit else '#dddddd',outline='#aaaaaa')
                value=n.findtext('ExtendedProperties/Link','') if edit else n.findtext('ExtendedProperties/LabelText','')
                font=ImageFont.truetype(str(FONT),13 if edit else 11)
                draw.text((x+6+(18 if check else 0),y+7),value,font=font,fill='#263740')
                if edit:controls.append((name,(x,y,x+w,y+h)))
    visit(scene)
    for name,(x1,y1,x2,y2) in texts:
        for control,(a,b,c,d) in controls:
            assert min(x2,c)<=max(x1,a) or min(y2,d)<=max(y1,b),(name,control,'overlapping caption/input')
    OUT.mkdir(exist_ok=True);im.save(OUT/f'vista_{tab}_diseno.png')
    print('Layout preview:',OUT/f'vista_{tab}_diseno.png')

if __name__=='__main__':
    render(0);render(3)
