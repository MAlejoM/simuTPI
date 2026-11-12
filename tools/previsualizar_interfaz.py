"""Render XML layout previews for spacing checks across all tabs and sub-tabs."""
from pathlib import Path
import xml.etree.ElementTree as E
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools/_workspace_visual_qa'
FONT = Path('C:/Windows/Fonts/arial.ttf')


def color(value):
    value = int(value or -1) & 0xffffff
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def render(tab, sub=0, guia=False, agent_name='Main'):
    tree = E.parse(ROOT / 'domitec_interactivo/Domitec_Interactivo.alp')
    main = next(a for a in tree.findall('Model/ActiveObjectClasses/ActiveObjectClass') if a.findtext('Name') == agent_name)
    scene = main.find('Presentation/Level/Presentation')
    im = Image.new('RGB', (1280, 1010), 'white')
    draw = ImageDraw.Draw(im)
    controls = []
    texts = []

    def group_visible(name):
        if agent_name == 'DomitecPlant':
            return name == 'guia_plano2D'
        if name.startswith('cuerpoVista'):
            return name == f'cuerpoVista{tab}'
        if name == 'guia3D_grupo':
            return guia
        if name.startswith('stats'):
            return name == ('statsSeries' if sub == 0 else 'statsResumen')
        if name.startswith('cfg'):
            return name == ['cfgPolitica', 'cfgDemanda', 'cfgPlanta'][sub]
        return True

    def rect_visible(name):
        checks = [
            ('tabActiva', f'tabActiva{tab}'),
            ('guia3D_activo_', 'guia3D_activo_0'),
            ('subTabStatsBar', f'subTabStatsBar{sub}'),
            ('subTabCfgBar', f'subTabCfgBar{sub}'),
            ('metricaICBar', 'metricaICBar0'),
            ('escenarioBar', 'escenarioBar0'),
            ('canalBar', 'canalBar0'),
            ('productoBar', 'productoBar0'),
            ('productoCfgBar', 'productoCfgBar0'),
        ]
        for prefix, active in checks:
            if name.startswith(prefix):
                return name == active
        if name == 'guia3DActivaBar':
            return guia
        return True

    def mock_expr(name, fallback):
        mocks = {
            'perfilFormUI': 'Editando: Maxiconsumo / Lavandina',
            'perfilPlantaUI': 'Producto seleccionado: Lavandina',
            'perfilActivoUI': 'Maxiconsumo / Lavandina',
            'tiempoUI': 'Semana 4.32 / 100  |  Semilla 1',
            'escenarioActivoUI': 'Escenario: 0 - Base 24x7  |  alfa=1.5  |  168 h/sem',
            'resumenRapidoUI': 'Fill Rate: 94.2%  |  Backlog: 12,400  |  WIP: 18,000',
            'resumenPlano2DHeader': 'Stock: 146,000  |  Produccion: 320,000  |  Canceladas: 0',
            'warmupHeader': 'Warm-up: 15.0 sem',
            'warmupStatsBadge': 'Ventana post warm-up: desde semana 15.0',
            'varianzaLabel': 'Varianza = 124,590,944',
            'guia3D_seleccion': '1. Recepcion Parque',
            'resumenOperacionUI': '24x7 | Canceladas: 0 | Insumos almacenados: 36,000 | WIP liberado: 18,000',
            'estadoEstudioUI': 'Sin estudio ejecutado | 0/300',
            'tablaPareadosUI': 'Sin estudio completo.\nEjecutar las 100 ternas.\nLos IC se publican con 100 pares.',
            'escenarioResumenCfgUI': 'Escenario activo: 0 - Base 24x7\nAlfa (latigo): 1.5  |  Apertura: 168 h/sem\nWarm-up: 15.0 sem  |  Espera cancelacion: 30.0 d',
            'mensajeUItexto': 'Los cambios se aplican a los proximos pedidos y procesos.',
        }
        if name.startswith('planoLote'):
            return 'Lotes: 0'
        if name.startswith('planoStock'):
            return 'Stock: 146000 cajas'
        if name.startswith('planoBacklog'):
            return 'Backlog: 0 cajas'
        if name.startswith('kpiValor'):
            return '94.2%' if name == 'kpiValor0' else '12,400'
        if name == 'guia3D_descripcion':
            import json
            return json.loads((ROOT / 'tools/sectores_planta.json').read_text(encoding='utf8'))[0]['descripcion']
        return mocks.get(name, fallback)

    def visit(parent, dx=0, dy=0):
        for n in parent:
            name = n.findtext('Name', '')
            x = float(n.findtext('X', '0')) + dx
            y = float(n.findtext('Y', '0')) + dy
            if n.tag == 'Group':
                if group_visible(name):
                    visit(n.find('Presentation'), x, y)
            elif n.findtext('DrawMode') == 'SHAPE_DRAW_3D':
                continue
            elif n.tag == 'Rectangle':
                if not rect_visible(name):
                    continue
                w = float(n.findtext('Width', '0'))
                h = float(n.findtext('Height', '0'))
                draw.rectangle((x, y, x + w, y + h), fill=color(n.findtext('FillColor')), outline=color(n.findtext('LineColor')))
            elif n.tag == 'TimePlot':
                w = float(n.findtext('Width', '580'))
                h = float(n.findtext('Height', '350'))
                draw.rectangle((x, y, x + w, y + h), fill='#f7f9fa', outline='#c5d0d5')
                font = ImageFont.truetype(str(FONT), 13)
                draw.text((x + 16, y + 14), f'TimePlot: {name}', font=font, fill='#263740')
            elif n.tag == 'Text':
                value = n.findtext('Text', '')
                if n.find('TextCode') is not None:
                    value = mock_expr(name, value)
                font = ImageFont.truetype(str(FONT), int(n.findtext('Font/Size', '12')))
                draw.multiline_text((x, y), value, font=font, fill=color(n.findtext('Color')), spacing=2)
                if name.endswith('Label') or name in ['mediaLabel', 'sdLabel', 'tanqueLabel']:
                    texts.append((name, draw.multiline_textbbox((x, y), value, font=font, spacing=2)))
            elif n.tag == 'Control':
                if n.get('Type') == 'Window3D':
                    w = 918.0 if guia else float(n.findtext('Width', '1212'))
                    h = float(n.findtext('Height', '790'))
                    draw.rectangle((x, y, x + w, y + h), fill='#e4eaec', outline='#9aabad')
                    font = ImageFont.truetype(str(FONT), 18)
                    draw.text((x + 40, y + h / 2), f'VISTA 3D DE LA PLANTA ({int(w)}x{int(h)})', font=font, fill='#60737b')
                    continue
                b = n.find('BasicProperties')
                w = float(b.get('Width', '100'))
                h = float(b.get('Height', '28'))
                edit = n.get('Type') == 'EditBox'
                check = n.get('Type') == 'CheckBox'
                if check:
                    draw.rectangle((x, y + 5, x + 19, y + 19), outline='#555555')
                    w = 14
                else:
                    draw.rectangle((x, y, x + w, y + h), fill='white' if edit else '#dddddd', outline='#aaaaaa')
                value = n.findtext('ExtendedProperties/Link', '') if edit else n.findtext('ExtendedProperties/LabelText', '')
                font = ImageFont.truetype(str(FONT), 13 if edit else 11)
                draw.text((x + 6 + (18 if check else 0), y + 7), value, font=font, fill='#263740')
                if edit:
                    controls.append((name, (x, y, x + w, y + h)))

    visit(scene, -float(main.findtext('ClientAreaTopLeft/X', '0')), -float(main.findtext('ClientAreaTopLeft/Y', '0')))
    for name, (x1, y1, x2, y2) in texts:
        for control, (a, b, c, d) in controls:
            assert min(x2, c) <= max(x1, a) or min(y2, d) <= max(y1, b), (name, control, 'overlapping caption/input')

    OUT.mkdir(exist_ok=True)
    if agent_name != 'Main':
        filename = 'domitecplant_2d_diseno.png'
    elif tab == 0 and guia:
        filename = 'vista_0_3d_guia.png'
    elif tab in (2, 3):
        filename = f'vista_{tab}_sub_{sub}.png'
    else:
        filename = f'vista_{tab}_diseno.png'
    im.save(OUT / filename)
    print('Layout preview:', OUT / filename)


if __name__ == '__main__':
    render(0)
    render(1)
    render(2, sub=0)
    render(2, sub=1)
    render(3, sub=0)
    render(3, sub=1)
    render(3, sub=2)
