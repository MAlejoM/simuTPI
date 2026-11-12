"""Modularize Main's presentation into a clean 3D-first layout with sub-tabs.

Preserves simulation logic, experiments, DomitecPlant geometry/markers,
Main variables, datasets, events, and all editable control bindings.
"""
from pathlib import Path
from xml.dom import minidom as D
import json
import re
import shutil
import tempfile
from crear_interfaz import children, text, put, code

ROOT = Path(__file__).resolve().parents[1]
ALP = ROOT / 'domitec_interactivo/Domitec_Interactivo.alp'

INK = -15193551
TEAL = -14381747
ACCENT = -11546643
BG = -658189
BORDER = -1906964
MUTED = -9603453
WHITE = -1


def _strip_var_decls(source: str) -> str:
    return re.sub(
        r'^public (?:double uiMedia|double uiLatigo|double uiEspera|int uiMaxWip|int uiReactores|String carpetaResultados).*?;\r?\n',
        '',
        source,
        flags=re.M,
    )


def _guia_planta_java(sectors: list) -> str:
    java_strings = lambda values: 'new String[]{' + ','.join(json.dumps(v, ensure_ascii=False) for v in values) + '}'
    names = java_strings([f'{i + 1}. {s["nombre"]}' for i, s in enumerate(sectors)])
    descriptions = java_strings([s['descripcion'] for s in sectors])
    centers = 'new double[][]{' + ','.join(
        '{' + str(s['area'][0] + s['area'][2] / 2) + ',' + str(s['area'][1] + s['area'][3] / 2) + '}'
        for s in sectors
    ) + '}'
    return f'''
// GUIA_PLANTA: presentation state only; it never changes production.
public int sector3DActivo=0;
public String nombreSector3D(){{return ({names})[sector3DActivo];}}
public String descripcionSector3D(){{return ({descriptions})[sector3DActivo];}}
public void enfocarSector3D(){{
    double[] c=({centers})[sector3DActivo];
    ventanaPlanta3D.setCamera(new com.anylogic.engine.presentation.Camera3D(c[0],c[1],600,Math.PI/2,0),false,0L);
}}
'''


def modularizar(d):
    model = children(d.documentElement, 'Model')[0]
    agents = {text(a, 'Name'): a for a in children(children(model, 'ActiveObjectClasses')[0], 'ActiveObjectClass')}
    main = agents['Main']
    scene = children(children(children(main, 'Presentation')[0], 'Level')[0], 'Presentation')[0]

    def byname(name):
        return next(n for n in scene.getElementsByTagName('*') if text(n, 'Name') == name)

    uid = max(int(n.firstChild.data.strip()) for n in d.getElementsByTagName('Id')
              if n.firstChild and n.firstChild.data.strip().isdigit()) + 10

    def fresh(n):
        nonlocal uid
        for e in [n] + list(n.getElementsByTagName('*')):
            if getattr(e, 'tagName', None) == 'Id':
                uid += 1
                while e.firstChild:
                    e.removeChild(e.firstChild)
                e.appendChild(d.createTextNode(str(uid)))
        return n

    # Capture reusable templates & preserved domain widgets before rebuilding Main scene.
    tpl_rect = byname('fondoUI').cloneNode(True)
    tpl_txt = byname('mediaLabel').cloneNode(True)
    tpl_btn = byname('editarLogicaUI').cloneNode(True)
    tpl_edit = byname('campoMedia').cloneNode(True)
    tpl_check = byname('operariosUI').cloneNode(True)
    tpl_window3d = byname('ventanaPlanta3D').cloneNode(True)
    tpl_camera = byname('camaraMain').cloneNode(True)
    tpl_group = byname('cuerpoVista1').cloneNode(True)
    while children(tpl_group, 'Presentation')[0].firstChild:
        p = children(tpl_group, 'Presentation')[0]
        p.removeChild(p.firstChild)

    plots = {name: byname(name).cloneNode(True) for name in ['plot', 'plot1', 'plot2', 'plotWip']}
    plano_group = byname('cuerpoVista0')
    plano_nodes = [n.cloneNode(True) for n in children(children(plano_group, 'Presentation')[0])]

    while scene.firstChild:
        scene.removeChild(scene.firstChild)

    def strip_codes(n):
        for c in list(children(n)):
            if c.tagName.endswith('Code'):
                n.removeChild(c)

    def group(parent, name, visible=None):
        n = tpl_group.cloneNode(True)
        fresh(n)
        strip_codes(n)
        for k, v in {'Name': name, 'X': 0, 'Y': 0, 'Z': 0, 'Rotation': 0,
                     'DrawMode': 'SHAPE_DRAW_2D', 'PublicFlag': 'true',
                     'PresentationFlag': 'true', 'ShowLabel': 'false'}.items():
            put(n, k, v)
        if visible is not None:
            code(n, 'VisibleCode', visible)
        parent.appendChild(n)
        return children(n, 'Presentation')[0]

    def panel(parent, name, x, y, w, h, color, line=None):
        n = tpl_rect.cloneNode(True)
        fresh(n)
        strip_codes(n)
        for k, v in {'Name': name, 'X': x, 'Y': y, 'Width': w, 'Height': h,
                     'Z': 0, 'ZHeight': 0, 'DrawMode': 'SHAPE_DRAW_2D',
                     'EmbeddedIcon': 'false', 'FillColor': color,
                     'LineColor': color if line is None else line,
                     'LineWidth': 1 if line is not None else 0}.items():
            put(n, k, v)
        parent.appendChild(n)
        return n

    def label(parent, name, x, y, value, size=12, color=INK, expr=None):
        n = tpl_txt.cloneNode(True)
        fresh(n)
        strip_codes(n)
        for k, v in {'Name': name, 'X': x, 'Y': y, 'Z': 0,
                     'DrawMode': 'SHAPE_DRAW_2D', 'EmbeddedIcon': 'false',
                     'Color': color, 'Text': value, 'Alignment': 'LEFT'}.items():
            put(n, k, v)
        font = children(n, 'Font')[0]
        put(font, 'Name', 'SansSerif')
        put(font, 'Size', size)
        put(font, 'Style', 0)
        if expr:
            code(n, 'TextCode', expr)
        parent.appendChild(n)
        return n

    def button(parent, name, x, y, w, h, value, action):
        n = tpl_btn.cloneNode(True)
        fresh(n)
        for k, v in {'Name': name, 'X': x, 'Y': y, 'DrawMode': 'SHAPE_DRAW_2D', 'ShowLabel': 'false'}.items():
            put(n, k, v)
        bp = children(n, 'BasicProperties')[0]
        bp.setAttribute('Width', str(w))
        bp.setAttribute('Height', str(h))
        code(bp, 'ActionCode', action)
        put(children(n, 'ExtendedProperties')[0], 'LabelText', value)
        parent.appendChild(n)
        return n

    def edit(parent, name, x, y, w, link):
        n = tpl_edit.cloneNode(True)
        fresh(n)
        for k, v in {'Name': name, 'X': x, 'Y': y, 'DrawMode': 'SHAPE_DRAW_2D', 'ShowLabel': 'false'}.items():
            put(n, k, v)
        bp = children(n, 'BasicProperties')[0]
        bp.setAttribute('Width', str(w))
        bp.setAttribute('Height', '30')
        ex = children(n, 'ExtendedProperties')[0]
        put(ex, 'Link', link)
        for font in children(ex, 'Font'):
            font.setAttribute('Name', 'SansSerif')
            font.setAttribute('Size', '13')
        parent.appendChild(n)
        return n

    def labeled_edit(parent, label_name, edit_name, x, y, w, title, link):
        label(parent, label_name, x, y, title, 12, INK)
        return edit(parent, edit_name, x, y + 25, w, link)

    # ------------------------------------------------------------------
    # Persistent chrome: Header (4 tabs) + 1 slim status strip + message
    # ------------------------------------------------------------------
    panel(scene, 'fondoUI', 0, 0, 1280, 1010, BG)
    panel(scene, 'cabeceraUI', 0, 0, 1280, 64, INK)
    label(scene, 'marcaUI', 24, 19, 'DOMITEC | SIMULACION DE PLANTA', 19, WHITE)

    top_tabs = [
        ('vista3D', 'Planta 3D'),
        ('vista2D', 'Flujo 2D'),
        ('estadisticas', 'Estadisticas'),
        ('logica', 'Configuracion'),
    ]
    for i, (ctrl_name, title) in enumerate(top_tabs):
        x = 620 + i * 158
        button(scene, ctrl_name, x, 17, 144, 30, title, f'mostrarVista({i});')
        bar = panel(scene, f'tabActiva{i}', x, 55, 144, 4, ACCENT)
        code(bar, 'VisibleCode', f'vistaActiva == {i}')

    panel(scene, 'statusBarUI', 24, 74, 1232, 34, WHITE, BORDER)
    label(
        scene, 'tiempoUI', 40, 84, 'Tiempo', 12, INK,
        expr='"Semana " + String.format(java.util.Locale.ROOT,"%.2f",time()) + " / 100  |  Semilla " + semillaReplica',
    )
    label(
        scene, 'escenarioActivoUI', 330, 84, 'Escenario', 12, TEAL,
        expr='"Escenario: " + escenarioTexto() + "  |  alfa=" + cfg.factLatigo + "  |  " + numero(cfg.horas) + " h/sem"',
    )
    label(
        scene, 'resumenRapidoUI', 855, 84, 'Resumen', 12, INK,
        expr='"Fill Rate: " + (time()<cfg.calentamiento ? "Calent." : String.format(java.util.Locale.ROOT,"%.1f%%",100*registro.fillRate(cfg.calentamiento))) + "  |  Backlog: " + numero(backlogActual()) + "  |  WIP: " + numero(wipActual())',
    )

    # ------------------------------------------------------------------
    # Tab 0: Planta 3D (Default landing screen, clean viewport + toggleable guide)
    # ------------------------------------------------------------------
    v0 = group(scene, 'cuerpoVista0', 'vistaActiva == 0')
    panel(v0, 'fondoCuerpo0', 24, 120, 1232, 854, WHITE, BORDER)
    label(v0, 'tituloPlanta3D', 40, 139, 'PLANTA 3D | Vista en vivo', 13, TEAL)

    chk = tpl_check.cloneNode(True)
    fresh(chk)
    for k, v in {'Name': 'operariosUI', 'X': 330, 'Y': 137, 'DrawMode': 'SHAPE_DRAW_2D'}.items():
        put(chk, k, v)
    put(children(chk, 'ExtendedProperties')[0], 'Link', 'domitecPlant.animarOperarios')
    put(children(chk, 'ExtendedProperties')[0], 'LabelText', 'Recorridos de operarios')
    v0.appendChild(chk)

    button(v0, 'vistaSuperiorUI', 608, 132, 168, 30, 'Vista superior', 'vistaSuperior();')
    button(v0, 'restablecerCamaraUI', 788, 132, 194, 30, 'Perspectiva general', 'restablecerCamara();')
    button(v0, 'toggleGuia3DUI', 994, 132, 246, 30, 'Guia de sectores (1-9)', 'alternarGuia3D();')
    g3d_bar = panel(v0, 'guia3DActivaBar', 994, 163, 246, 3, TEAL)
    code(g3d_bar, 'VisibleCode', 'mostrarGuia3D')

    win = tpl_window3d.cloneNode(True)
    fresh(win)
    for k, v in {'Name': 'ventanaPlanta3D', 'X': 34, 'Y': 172, 'Width': 1212, 'Height': 790,
                 'MakeDefaultViewArea': 'false', 'Camera': 'camaraMain', 'FarClippingDistance': 4000}.items():
        put(win, k, v)
    v0.appendChild(win)

    sectors = json.loads((ROOT / 'tools/sectores_planta.json').read_text(encoding='utf8'))
    guia = group(v0, 'guia3D_grupo', 'mostrarGuia3D')
    panel(guia, 'guia3D_panel', 962, 172, 284, 790, BG, BORDER)
    label(guia, 'guia3D_titulo', 978, 188, 'GUIA DE SECTORES', 14, TEAL)
    for i, s in enumerate(sectors):
        y = 220 + i * 33
        button(guia, f'guia3D_sector_{i}', 978, y, 252, 27, f'{i + 1}. {s["nombre"]}', f'sector3DActivo={i};')
        bar = panel(guia, f'guia3D_activo_{i}', 970, y, 4, 27, ACCENT)
        code(bar, 'VisibleCode', f'sector3DActivo=={i}')
    label(guia, 'guia3D_seleccion', 978, 535, 'Sector', 14, TEAL, expr='nombreSector3D()')
    label(guia, 'guia3D_descripcion', 978, 566, 'Descripcion', 12, INK, expr='descripcionSector3D()')
    label(guia, 'guia3D_nota', 978, 725,
          'El sector seleccionado se marca\ncon un contorno en el piso.\n\nCada lote representa 1.000 cajas.',
          11, MUTED)
    button(guia, 'guia3D_enfocar', 978, 916, 252, 30, 'Acercar al sector', 'enfocarSector3D();')

    # ------------------------------------------------------------------
    # Tab 1: Flujo 2D (Clean process schematic)
    # ------------------------------------------------------------------
    v1 = group(scene, 'cuerpoVista1', 'vistaActiva == 1')
    panel(v1, 'fondoCuerpo1', 24, 120, 1232, 854, WHITE, BORDER)
    label(v1, 'tituloPlano2DHeader', 40, 136, 'FLUJO 2D | Recorrido de lotes en tiempo real', 14, TEAL)
    label(v1, 'subtituloPlano2DHeader', 40, 162,
          'Cada lote equivale a 1.000 cajas. Parque elabora Lavandina; Vicentin procesa cinco liquidos.',
          12, MUTED)
    label(
        v1, 'resumenPlano2DHeader', 760, 138, 'Totales', 12, INK,
        expr='"Stock: " + numero(stockActual()) + "  |  Produccion: " + numero(registro.produccionTotal(cfg.calentamiento)) + "  |  Canceladas: " + numero(canceladasActual())',
    )
    for node in plano_nodes:
        fresh(node)
        v1.appendChild(node)
    label(v1, 'notaPlano2DFooter', 40, 924,
          'Los contadores dentro de cada etapa indican lotes activos en cola, proceso, control de calidad o tanque pulmon.',
          11, MUTED)

    # ------------------------------------------------------------------
    # Tab 2: Estadisticas (Sub-tab 0: Series 2x2 | Sub-tab 1: KPIs & 100x3 CI)
    # ------------------------------------------------------------------
    v2 = group(scene, 'cuerpoVista2', 'vistaActiva == 2')
    panel(v2, 'fondoCuerpo2', 24, 120, 1232, 854, WHITE, BORDER)
    label(v2, 'tituloStats', 40, 138, 'ESTADISTICAS', 14, TEAL)
    for i, (ctrl_name, title, x, w) in enumerate([
        ('subTabStats0', 'Series temporales', 220, 210),
        ('subTabStats1', 'KPIs y Estudio 100x3', 444, 230),
    ]):
        button(v2, ctrl_name, x, 132, w, 30, title, f'subVistaStats={i};')
        bar = panel(v2, f'subTabStatsBar{i}', x, 164, w, 3, TEAL)
        code(bar, 'VisibleCode', f'subVistaStats == {i}')
    panel(v2, 'lineaStatsHeader', 40, 172, 1200, 1, BORDER)

    # Sub-tab 2.0: Series temporales
    s0 = group(v2, 'statsSeries', 'subVistaStats == 0')
    label(s0, 'warmupStatsBadge', 880, 139, 'Warm-up', 12, MUTED,
          expr='"Ventana post warm-up: desde semana " + cfg.calentamiento')
    for name, (x, y, w, h) in [
        ('plot', (40, 190, 588, 350)),
        ('plot1', (652, 190, 588, 350)),
        ('plot2', (40, 560, 588, 350)),
        ('plotWip', (652, 560, 588, 350)),
    ]:
        p = fresh(plots[name])
        for k, v in {'X': x, 'Y': y, 'Width': w, 'Height': h, 'DrawMode': 'SHAPE_DRAW_2D'}.items():
            put(p, k, v)
        chart = children(p, 'ChartArea')[0]
        put(chart, 'Width', w - 82)
        put(chart, 'Height', h - 88)
        s0.appendChild(p)
    label(s0, 'notaEstacionariaUI', 40, 932,
          'Calentamiento no implica estacionariedad: revisar las series semanales y su tendencia.',
          11, MUTED)

    # Sub-tab 2.1: KPIs y Estudio 100x3
    s1 = group(v2, 'statsResumen', 'subVistaStats == 1')
    label(s1, 'tituloKpisStats', 40, 190, 'INDICADORES DE LA CORRIDA ACTUAL (POST WARM-UP)', 13, TEAL)
    kpis = [
        ('Fill Rate', 'time()<cfg.calentamiento ? "Calentando" : String.format(java.util.Locale.ROOT,"%.2f%%",100*registro.fillRate(cfg.calentamiento))'),
        ('Backlog actual (cajas)', 'numero(backlogActual())'),
        ('Stock actual (cajas)', 'numero(stockActual())'),
        ('WIP en planta (cajas)', 'numero(wipActual())'),
        ('Produccion acumulada', 'numero(registro.produccionTotal(cfg.calentamiento))'),
        ('Razon Efecto Latigo (BW)', 'String.format(java.util.Locale.ROOT,"%.3f",registro.bw(cfg.calentamiento))'),
    ]
    for i, (title, expr) in enumerate(kpis):
        col, row = i % 3, i // 3
        kx = 40 + col * 404
        ky = 218 + row * 94
        panel(s1, f'kpiCard{i}', kx, ky, 386, 80, BG, BORDER)
        label(s1, f'kpiTitulo{i}', kx + 16, ky + 14, title, 11, MUTED)
        label(s1, f'kpiValor{i}', kx + 16, ky + 40, '0', 21, TEAL, expr=expr)

    panel(s1, 'panelOperacion24x7', 40, 410, 1194, 38, BG, BORDER)
    label(
        s1, 'resumenOperacionUI', 56, 421, 'Operacion 24x7', 12, INK,
        expr='"24x7 | Canceladas: "+numero(canceladasActual())+" | Insumos almacenados: "+numero(insumosActual())+" | WIP liberado: "+numero(wipActual())',
    )

    panel(s1, 'panelPareados', 40, 466, 1194, 488, BG, BORDER)
    label(s1, 'tituloPareadosUI', 60, 486, 'ESTUDIO PAREADO | 100 SEMILLAS x 3 ESCENARIOS (IC 95%)', 13, TEAL)
    button(s1, 'estudioUI', 762, 478, 260, 30, 'Guardar parametros para estudio', 'ejecutarComparacion();')
    button(s1, 'detenerEstudioUI', 1036, 478, 178, 30, 'Leer ultimos IC', 'cargarUltimosIC();')
    label(s1, 'estadoEstudioUI', 60, 522, 'Estado', 12, MUTED,
          expr='SesionEstudio.estado + " | " + SesionEstudio.progreso + "/300"')
    for j, (title, metric) in enumerate([('Servicio', 0), ('Backlog', 1), ('Latigo', 2)]):
        bx = 60 + j * 136
        button(s1, f'metricaIC{j}', bx, 556, 124, 30, title, f'metricaIC={metric};')
        mbar = panel(s1, f'metricaICBar{j}', bx, 588, 124, 3, TEAL)
        code(mbar, 'VisibleCode', f'metricaIC == {metric}')
    label(s1, 'tablaPareadosUI', 60, 608, 'IC pareados', 13, INK, expr='tablaIC()')
    panel(s1, 'panelGuiaEstudio', 630, 556, 584, 376, WHITE, BORDER)
    label(s1, 'tituloGuiaEstudio', 650, 578, 'FLUJO DE COMPARACION 100 x 3', 13, TEAL)
    label(
        s1, 'textoGuiaEstudio', 650, 616,
        '1. En AnyLogic, abrir el experimento Comparacion_100x3.\n\n'
        '2. Para usar los escenarios estandar 24x7, ejecutarlo directo.\n'
        '   Si modificaste parametros aqui, pulsar antes\n'
        '   "Guardar parametros para estudio".\n\n'
        '3. Al completar las 300 corridas, volver a esta pestana y\n'
        '   pulsar "Leer ultimos IC" para ver las diferencias pareadas.\n\n'
        'Nota: los intervalos se calculan sobre las 100 ternas\n'
        'pareadas por semilla (CRN) despues del calentamiento.',
        12, MUTED,
    )

    # ------------------------------------------------------------------
    # Tab 3: Configuracion (Sub-tabs: Politica | Demanda | Planta)
    # ------------------------------------------------------------------
    v3 = group(scene, 'cuerpoVista3', 'vistaActiva == 3')
    panel(v3, 'fondoCuerpo3', 24, 120, 1232, 854, WHITE, BORDER)
    label(v3, 'tituloConfigUI', 40, 138, 'CONFIGURACION', 14, TEAL)
    for i, (ctrl_name, title, x, w) in enumerate([
        ('subTabCfg0', '1. Escenario y Politica', 220, 220),
        ('subTabCfg1', '2. Demanda por Perfil', 454, 220),
        ('subTabCfg2', '3. Planta y Capacidad', 688, 220),
    ]):
        button(v3, ctrl_name, x, 132, w, 30, title, f'subVistaConfig={i};')
        bar = panel(v3, f'subTabCfgBar{i}', x, 164, w, 3, TEAL)
        code(bar, 'VisibleCode', f'subVistaConfig == {i}')
    panel(v3, 'lineaCfgHeader', 40, 172, 1200, 1, BORDER)

    # Sub-tab 3.0: Escenario y Politica
    c0 = group(v3, 'cfgPolitica', 'subVistaConfig == 0')
    panel(c0, 'card_escenarios_cfg', 40, 194, 578, 550, BG, BORDER)
    label(c0, 'tituloEscenarios', 60, 214, 'ESCENARIO ACTIVO', 14, TEAL)
    scenarios_ui = [
        ('0 - Base 24x7', 'Operacion continua 168 h/sem\nFactor latigo alfa = 1.5'),
        ('1 - Sin panico', 'Elimina amplificacion (alfa = 1.0)\nMantiene operacion 24x7'),
        ('2 - Rendim. +27.5%', 'Sin panico (alfa = 1.0) +\nhipotesis +27,5% rendimiento'),
    ]
    for i, (title, desc) in enumerate(scenarios_ui):
        sy = 258 + i * 82
        button(c0, f'escenarioUI{i}', 60, sy, 236, 34, title, f'elegirEscenario({i});')
        sbar = panel(c0, f'escenarioBar{i}', 60, sy + 36, 236, 3, ACCENT)
        code(sbar, 'VisibleCode', f'escenarioActivo == {i}')
        label(c0, f'escenarioDesc{i}', 312, sy, desc, 12, MUTED)

    panel(c0, 'card_escenario_resumen', 60, 520, 538, 120, WHITE, BORDER)
    label(
        c0, 'escenarioResumenCfgUI', 76, 536, 'Resumen', 12, INK,
        expr='"Escenario activo: " + escenarioTexto() + "\\nAlfa (latigo): " + cfg.factLatigo + "  |  Apertura: " + numero(cfg.horas) + " h/sem\\nWarm-up: " + cfg.calentamiento + " sem  |  Espera cancelacion: " + cfg.esperaPedidoDias + " d"',
    )

    panel(c0, 'card_politica_cfg', 642, 194, 594, 550, BG, BORDER)
    label(c0, 'tituloPoliticaUI', 662, 214, 'REGLAS DE FLUJO Y POLITICA', 14, TEAL)
    labeled_edit(c0, 'campoLatigoLabel', 'campoLatigo', 662, 258, 550, 'Factor latigo (alfa)', 'uiLatigo')
    labeled_edit(c0, 'esperaLabel', 'campoEspera', 662, 336, 550, 'Cancelacion: espera SUPUESTA (dias)', 'uiEspera')
    labeled_edit(c0, 'maxWipLabel', 'campoMaxWip', 662, 414, 550, 'Limite PROVISIONAL de lotes liberados (WIP max)', 'uiMaxWip')
    labeled_edit(c0, 'campoWarmupLabel', 'campoWarmup', 662, 492, 550, 'Calentamiento (0 a <100 semanas)', 'uiWarmup')
    button(c0, 'aplicarPoliticaUI', 662, 578, 550, 34, 'Aplicar reglas y politica', 'guardarPlanta();')
    label(c0, 'notaPoliticaUI', 662, 628,
          'Los lotes ya iniciados conservan sus tiempos sorteados.\nEl limite WIP debe ser mayor o igual al WIP presente.',
          11, MUTED)

    panel(c0, 'card_export_cfg', 40, 764, 1196, 150, BG, BORDER)
    label(c0, 'tituloExportUI', 60, 782, 'EXPORTACION DE RESULTADOS CSV (COMPARACION 100 x 3)', 13, TEAL)
    labeled_edit(c0, 'rutaCSVLabel', 'campoCarpeta', 60, 818, 1152, 'Carpeta de resultados CSV', 'carpetaResultados')

    # Sub-tab 3.1: Demanda por Perfil
    c1 = group(v3, 'cfgDemanda', 'subVistaConfig == 1')
    panel(c1, 'card_demanda', 40, 194, 560, 660, BG, BORDER)
    label(c1, 'tituloDemandaUI', 60, 214, 'PERFIL CANAL x PRODUCTO', 14, TEAL)
    label(c1, 'subtituloCanalUI', 60, 252, '1. Canal comercial', 12, MUTED)
    for c, title in enumerate(['Maxiconsumo', 'Grandes cli.', 'Red propia']):
        cx = 60 + c * 176
        button(c1, f'canalUI{c}', cx, 276, 166, 32, title, f'seleccionarPerfil({c},perfilProducto);')
        cbar = panel(c1, f'canalBar{c}', cx, 310, 166, 3, TEAL)
        code(cbar, 'VisibleCode', f'perfilCanal == {c}')

    label(c1, 'subtituloProdUI', 60, 342, '2. Producto', 12, MUTED)
    products = ['Lavandina', 'Desinfectante', 'Lavavajilla', 'Lavarropa', 'Suavizante', 'Detergente']
    for p, title in enumerate(products):
        px = 60 + (p % 2) * 260
        py = 368 + (p // 2) * 48
        button(c1, f'productoUI{p}', px, py, 248, 34, title, f'seleccionarPerfil(perfilCanal,{p});')
        pbar = panel(c1, f'productoBar{p}', px, py + 36, 248, 3, TEAL)
        code(pbar, 'VisibleCode', f'perfilProducto == {p}')

    label(c1, 'perfilFormUI', 60, 536, 'Perfil', 14, TEAL, expr='"Editando: " + perfilTexto()')
    label(c1, 'notaDemandaUI', 60, 580,
          'Meses de 2025 remuestreados.\nVariacion mensual; no mide picos diarios.\n\n'
          'El sorteo depende de semilla, canal,\nproducto y semana; no del orden\nde los eventos de produccion.',
          12, MUTED)

    panel(c1, 'card_demanda_valores', 624, 194, 612, 660, BG, BORDER)
    label(c1, 'tituloDemandaValoresUI', 644, 214, 'PARAMETROS DE DEMANDA DEL PERFIL', 14, TEAL)
    labeled_edit(c1, 'mediaLabel', 'campoMedia', 644, 266, 260, 'Media (cajas / semana)', 'uiMedia')
    labeled_edit(c1, 'sdLabel', 'campoDesvio', 932, 266, 260, 'Desvio estandar', 'uiDesvio')
    label(c1, 'varianzaLabel', 644, 344, 'Varianza', 12, MUTED,
          expr='"Varianza = " + numero(uiDesvio*uiDesvio)')
    button(c1, 'aplicarDemandaUI', 644, 386, 548, 34, 'Aplicar demanda al perfil seleccionado', 'guardarDemanda();')

    # Sub-tab 3.2: Planta y Capacidad
    c2 = group(v3, 'cfgPlanta', 'subVistaConfig == 2')
    panel(c2, 'card_inventario', 40, 194, 586, 650, BG, BORDER)
    label(c2, 'tituloInventarioUI', 60, 214, 'INVENTARIO Y CAPACIDAD', 14, TEAL)
    for p, title in enumerate(products):
        px = 60 + (p % 3) * 184
        py = 246 + (p // 3) * 38
        button(c2, f'productoCfgUI{p}', px, py, 176, 28, title, f'seleccionarPerfil(perfilCanal,{p});')
        pbar = panel(c2, f'productoCfgBar{p}', px, py + 30, 176, 3, TEAL)
        code(pbar, 'VisibleCode', f'perfilProducto == {p}')
    label(c2, 'perfilPlantaUI', 60, 326, 'Producto', 12, TEAL,
          expr='"Producto seleccionado: " + nombreProducto(perfilProducto)')

    for j, (lab, name, link) in enumerate([
        ('Horas de apertura / semana (max. 168)', 'campoHoras', 'uiHoras'),
        ('Lead time (dias, producto)', 'campoLead', 'uiLead'),
        ('Cobertura (semanas, producto)', 'campoCobertura', 'uiCobertura'),
        ('Ritmo efectivo (cajas/h de apertura)', 'campoRate', 'uiRate'),
        ('Multiplicador de capacidad', 'campoCapacidad', 'uiCapacidad'),
    ]):
        labeled_edit(c2, name + 'Label', name, 60, 360 + j * 90, 546, lab, link)

    panel(c2, 'card_proceso', 650, 194, 586, 650, BG, BORDER)
    label(c2, 'tituloProcesoUI', 670, 214, 'PROCESO, MERMAS Y RECURSOS', 14, TEAL)
    for j, (lab, label_name, name, link) in enumerate([
        ('Rechazo adicional lavandina (%)', 'campoMermaLavLabel', 'campoMermaLav', 'uiMermaLav'),
        ('Rechazo adicional liquidos (%)', 'campoMermaLiqLabel', 'campoMermaLiq', 'uiMermaLiq'),
        ('Factor de tiempos de proceso', 'campoTiempoLabel', 'campoTiempo', 'uiTiempo'),
        ('Reactores en paralelo', 'campoReactoresLabel', 'campoReactores', 'uiReactores'),
        ('Capacidad cola de elaboracion (lotes)', 'campoColaLabel', 'campoCola', 'uiCola'),
        ('Capacidad de cada tanque (lotes)', 'tanqueLabel', 'campoTanque', 'uiTanque'),
    ]):
        labeled_edit(c2, label_name, name, 670, 256 + j * 92, 546, lab, link)

    button(c2, 'aplicarPlantaUI', 40, 864, 1196, 34, 'Aplicar parametros de planta y medicion', 'guardarPlanta();')

    # 3D camera + quiet footer message
    scene.appendChild(fresh(tpl_camera))
    label(scene, 'mensajeUItexto', 24, 986, 'Mensaje', 11, MUTED, expr='mensajeUI')

    # Update Main AdditionalClassCode cleanly, keeping GUIA_PLANTA helpers.
    additional = _strip_var_decls((ROOT / 'tools/MainInterfaz.code.java.txt').read_text(encoding='utf8'))
    code(main, 'AdditionalClassCode', additional + _guia_planta_java(sectors))


def main():
    backup = Path(tempfile.mkdtemp(prefix='domitec-antes-modularizar-'))
    shutil.copy2(ALP, backup / ALP.name)
    d = D.parse(str(ALP))
    modularizar(d)
    ALP.write_bytes(d.toxml(encoding='UTF-8'))
    print('Updated', ALP)
    print('Backup:', backup)


if __name__ == '__main__':
    main()
