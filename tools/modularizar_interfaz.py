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
ACCENT = -14381747
BG = -328966
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
public int sector3DActivo=-1;
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
    original_ids = {text(n, 'Name'): text(n, 'Id') for n in scene.getElementsByTagName('*')
                    if text(n, 'Name') and text(n, 'Id')}

    def byname(name):
        return next(n for n in scene.getElementsByTagName('*') if text(n, 'Name') == name)

    def byname_any(names):
        for name in names:
            found = next((n for n in scene.getElementsByTagName('*') if text(n, 'Name') == name), None)
            if found is not None:
                return found
        raise StopIteration(names)

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
    tpl_btn = byname_any(['editarLogicaUI', 'restablecerCamaraUI']).cloneNode(True)
    tpl_edit = byname('campoMedia').cloneNode(True)
    tpl_window3d = byname('ventanaPlanta3D').cloneNode(True)
    tpl_camera = byname('camaraMain').cloneNode(True)
    tpl_group = byname('cuerpoVista1').cloneNode(True)
    while children(tpl_group, 'Presentation')[0].firstChild:
        p = children(tpl_group, 'Presentation')[0]
        p.removeChild(p.firstChild)

    plots = {name: byname(name).cloneNode(True) for name in ['plot', 'plot1', 'plot2', 'plotWip']}

    while scene.firstChild:
        scene.removeChild(scene.firstChild)

    def strip_codes(n):
        for c in list(children(n)):
            if c.tagName.endswith('Code'):
                n.removeChild(c)

    def group(parent, name, visible=None, editor_x=0, editor_y=0):
        n = tpl_group.cloneNode(True)
        fresh(n)
        strip_codes(n)
        for k, v in {'Name': name, 'X': editor_x, 'Y': editor_y, 'Z': 0, 'Rotation': 0,
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
        put(font, 'Size', max(16, size + 2 if size >= 16 else size))
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
        bp.setAttribute('Height', str(max(34, h)))
        code(bp, 'ActionCode', action)
        put(children(n, 'ExtendedProperties')[0], 'LabelText', value)
        for font in children(children(n, 'ExtendedProperties')[0], 'Font'):
            font.setAttribute('Name', 'SansSerif')
            font.setAttribute('Size', '16')
        parent.appendChild(n)
        return n

    def edit(parent, name, x, y, w, link):
        n = tpl_edit.cloneNode(True)
        fresh(n)
        for k, v in {'Name': name, 'X': x, 'Y': y, 'DrawMode': 'SHAPE_DRAW_2D', 'ShowLabel': 'false'}.items():
            put(n, k, v)
        bp = children(n, 'BasicProperties')[0]
        bp.setAttribute('Width', str(w))
        bp.setAttribute('Height', '34')
        ex = children(n, 'ExtendedProperties')[0]
        put(ex, 'Link', link)
        for font in children(ex, 'Font'):
            font.setAttribute('Name', 'SansSerif')
            font.setAttribute('Size', '16')
        parent.appendChild(n)
        return n

    def labeled_edit(parent, label_name, edit_name, x, y, w, title, link):
        label(parent, label_name, x, y, title, 12, INK)
        return edit(parent, edit_name, x, y + 25, w, link)

    # ------------------------------------------------------------------
    # Persistent chrome: Header (4 tabs) + 1 slim status strip + message
    # ------------------------------------------------------------------
    panel(scene, 'fondoUI', 0, 0, 1280, 1010, WHITE)
    panel(scene, 'cabeceraUI', 0, 0, 1280, 64, WHITE)
    label(scene, 'marcaUI', 28, 20, 'DOMITEC', 20, INK)
    label(scene, 'submarcaUI', 150, 25, 'Simulación de planta', 13, MUTED)

    top_tabs = [
        ('vista3D', 'Planta 3D'),
        ('vista2D', 'Proceso 2D'),
        ('estadisticas', 'Estadísticas'),
        ('logica', 'Configuración'),
    ]
    for i, (ctrl_name, title) in enumerate(top_tabs):
        x = 28 + i * 250
        button(scene, ctrl_name, x, 70, 232, 36, title, f'mostrarVista({i});')
        bar = panel(scene, f'tabActiva{i}', x, 110, 232, 4, ACCENT)
        code(bar, 'VisibleCode', f'vistaActiva == {i}')

    label(
        scene, 'tiempoUI', 28, 132, 'Tiempo', 13, INK,
        expr='"Semana " + String.format(java.util.Locale.ROOT,"%.2f",time()) + " / 100  |  Semilla " + semillaReplica',
    )
    label(
        scene, 'escenarioActivoUI', 620, 132, 'Escenario', 13, MUTED,
        expr='"Escenario " + escenarioTexto() + "  ·  " + numero(cfg.horas) + " h/semana"',
    )
    panel(scene, 'separadorEstadoUI', 28, 164, 1224, 1, BORDER)

    # ------------------------------------------------------------------
    # Tab 0: Planta 3D (Default landing screen, clean viewport)
    # ------------------------------------------------------------------
    v0 = group(scene, 'cuerpoVista0', 'vistaActiva == 0')
    button(v0, 'vistaSuperiorUI', 792, 322, 200, 36, 'Vista superior', 'vistaSuperior();')
    button(v0, 'restablecerCamaraUI', 1006, 322, 248, 36, 'Perspectiva general', 'restablecerCamara();')
    label(v0, 'referenciasParque3D', 28, 184, 'Parque · Lavandina', 17, TEAL)
    label(v0, 'referenciasVicentin3D', 620, 184, 'Vicentin · Líquidos', 17, TEAL)
    for number, x, y, title in [
        (1,28,222,'Recepción'), (2,28,250,'Dilución y calidad'),
        (3,28,278,'Envasado'), (4,320,222,'Depósito'),
        (5,620,222,'Recepción'), (6,620,250,'Reactores y calidad'),
        (7,620,278,'Tanques pulmón'), (8,930,222,'Envasado'),
        (9,930,250,'Depósito'),
    ]:
        label(v0, 'referencia3D' + str(number), x, y, f'{number}  {title}', 14, INK)

    win = tpl_window3d.cloneNode(True)
    fresh(win)
    for k, v in {'Name': 'ventanaPlanta3D', 'X': 0, 'Y': 374, 'Width': 1280, 'Height': 636,
                 'MakeDefaultViewArea': 'false', 'Camera': 'camaraMain', 'FarClippingDistance': 4000}.items():
        put(win, k, v)
    v0.appendChild(win)

    sectors = json.loads((ROOT / 'tools/sectores_planta.json').read_text(encoding='utf8'))

    # ------------------------------------------------------------------
    # Tab 1: Flujo 2D (Clean process schematic)
    # ------------------------------------------------------------------
    v1 = group(scene, 'cuerpoVista1', 'vistaActiva == 1', editor_x=1400)
    label(v1, 'tituloPlano2DHeader', 28, 184, 'Proceso de producción', 18, INK)
    label(v1, 'subtituloPlano2DHeader', 28, 220,
          'Seguí las flechas. Los contadores muestran lotes activos; cada lote equivale a 1.000 cajas.',
          13, MUTED)
    from plano_2d_resumido import crear_plano_resumido
    def label_2d(parent, name, x, y, value, size=16, color=INK, expr=None):
        n = label(parent, name, x, y, value, size, color, expr)
        put(children(n, 'Font')[0], 'Size', max(15, size - 1))
        return n
    crear_plano_resumido(v1, panel, label_2d)
    for n in children(v1):
        if text(n, 'Name').startswith('plano'):
            put(n, 'Y', 252 + (float(text(n, 'Y')) - 200) * .90)
            if n.tagName == 'Rectangle':
                put(n, 'Height', float(text(n, 'Height')) * .90)
                if text(n, 'Name') == 'planoFondo':
                    put(n, 'LineWidth', 0)

    # ------------------------------------------------------------------
    # Tab 2: Estadisticas (Sub-tab 0: Series 2x2 | Sub-tab 1: KPIs & 100x3 CI)
    # ------------------------------------------------------------------
    v2 = group(scene, 'cuerpoVista2', 'vistaActiva == 2', editor_x=2800)
    label(v2, 'tituloStats', 28, 184, 'Estadísticas', 18, INK)
    for i, (ctrl_name, title, x, w) in enumerate([
        ('subTabStats0', 'Gráficos', 260, 200),
        ('subTabStats1', 'Indicadores', 474, 200),
        ('subTabStats2', 'Comparar escenarios', 688, 230),
    ]):
        x -= 232
        button(v2, ctrl_name, x, 222, w, 34, title, f'subVistaStats={i};')
        bar = panel(v2, f'subTabStatsBar{i}', x, 260, w, 3, TEAL)
        code(bar, 'VisibleCode', f'subVistaStats == {i}')
    panel(v2, 'lineaStatsHeader', 28, 272, 1224, 1, BORDER)

    # Sub-tab 2.0: Series temporales
    s0 = group(v2, 'statsSeries', 'subVistaStats == 0')
    for name, title, unit, (x, y, w, h) in [
        ('plot', 'Demanda y compras al proveedor', 'Cajas / semana', (40, 212, 588, 324)),
        ('plot1', 'Producción terminada', 'Cajas / semana', (652, 212, 588, 324)),
        ('plot2', 'Pedidos pendientes', 'Cajas pendientes', (40, 588, 588, 324)),
        ('plotWip', 'Cajas en proceso', 'Cajas en proceso', (652, 588, 588, 324)),
    ]:
        p = fresh(plots[name])
        for k, v in {'X': x, 'Y': y, 'Width': w, 'Height': h, 'DrawMode': 'SHAPE_DRAW_2D'}.items():
            put(p, k, v)
        chart = children(p, 'ChartArea')[0]
        put(chart, 'XOffset', 76)
        put(chart, 'YOffset', 32)
        put(chart, 'Width', w - 98)
        put(chart, 'Height', h - 116)
        put(chart, 'BorderColor', BORDER)
        put(chart, 'GridColor', -1513240)
        put(children(p, 'Legend')[0], 'TextColor', INK)
        put(children(p, 'Legend')[0], 'Size', 24)
        put(children(p, 'Labels')[0], 'TextColor', MUTED)
        for dataset in children(p, 'DatasetExpression'):
            expr = text(dataset, 'Expression')
            put(dataset, 'Title', {
                'dsDemanda': 'Demanda de clientes', 'dsOrdenes': 'Compras al proveedor',
                'dsProduccionSemanal': 'Producción', 'dsBacklog': 'Pedidos pendientes',
                'dsWip': 'En proceso',
            }[expr])
            palette = {'dsDemanda': 0x3473A5, 'dsOrdenes': 0xC2873E,
                       'dsProduccionSemanal': 0x26806E, 'dsBacklog': 0xB4753B,
                       'dsWip': 0x8E52A5}
            put(dataset, 'Color', palette[expr] - 0x1000000)
            put(dataset, 'LineWidth', 2)
        s0.appendChild(p)
        label(s0, name + 'Titulo', x, y - 26, title, 15, INK)
        # Axis names are ordinary supported Text shapes, placed outside tick labels
        # and above the native legend. No unsupported TimePlot XML tags are used.
        label(s0, name + 'EjeY', x + 6, y + 8, unit, 12, MUTED)
        label(s0, name + 'EjeX', x + 228, y + h - 56, 'Tiempo (semanas)', 12, MUTED)
    label(s0, 'notaEstacionariaUI', 40, 932,
          'Las series muestran toda la corrida. Los indicadores excluyen las semanas iniciales de calentamiento.',
          13, MUTED)

    # Sub-tab 2.1: KPIs y Estudio 100x3
    s1 = group(v2, 'statsResumen', 'subVistaStats == 1', editor_y=1100)
    label(s1, 'tituloKpisStats', 40, 200, 'Resultado de esta corrida', 18, INK)
    label(s1, 'periodoIndicadoresUI', 40, 234, 'Período de medición', 13, MUTED,
          expr='"Servicio, producción y efecto látigo: desde la semana " + numero(cfg.calentamiento) + ". Los demás valores muestran el estado actual."')
    kpis = [
        ('Demanda atendida (%)', 'time()<cfg.calentamiento ? "Calentando" : String.format(java.util.Locale.ROOT,"%.2f%%",100*registro.fillRate(cfg.calentamiento))',
         'Porcentaje entregado, incluso con demora.\nNo mide puntualidad de entrega.'),
        ('Pedidos pendientes (cajas)', 'numero(backlogActual())',
         'Demanda que todavía espera entrega.\nNo incluye pedidos ya cancelados.'),
        ('Stock terminado (cajas)', 'numero(stockActual())',
         'Cajas listas para entregar\nque permanecen en el depósito.'),
        ('Cajas en proceso', 'numero(wipActual())',
         'Lotes liberados que aún no terminaron.\nIncluye colas y tanques; excluye insumos.'),
        ('Producción terminada (cajas)', 'numero(registro.produccionTotal(cfg.calentamiento))',
         'Cajas producidas desde el inicio\ndel período de medición.'),
        ('Efecto látigo (razón)', 'String.format(java.util.Locale.ROOT,"%.3f",registro.bw(cfg.calentamiento))',
         'Varianza de compras / varianza de demanda.\nMayor que 1: las compras varían más.'),
    ]
    for i, (title, expr, meaning) in enumerate(kpis):
        col, row = i % 3, i // 3
        kx = 40 + col * 404
        ky = 280 + row * 194
        panel(s1, f'kpiCard{i}', kx, ky, 386, 174, BG)
        label(s1, f'kpiTitulo{i}', kx + 18, ky + 18, title, 14, INK)
        label(s1, f'kpiValor{i}', kx + 18, ky + 52, '0', 26, TEAL, expr=expr)
        label(s1, f'kpiAyuda{i}', kx + 18, ky + 109, meaning, 13, MUTED)

    panel(s1, 'panelOperacion24x7', 40, 686, 1194, 84, BG)
    label(
        s1, 'resumenOperacionUI', 58, 704, 'Otros valores', 14, INK,
        expr='"Pedidos cancelados: " + numero(canceladasActual()) + " cajas  ·  Insumos almacenados: " + numero(insumosActual()) + " cajas equivalentes"',
    )
    label(s1, 'otrosIndicadoresNota', 58, 738,
          'Cancelaciones: desde el inicio de la corrida. Insumos: saldo actual, expresado como cajas que permitirían producir.', 13, MUTED)
    label(s1, 'notaIndicadoresUI', 40, 814,
          'Cada corrida es un resultado posible. Para comparar políticas usá la pestaña Comparar escenarios.', 13, MUTED)

    s2 = group(v2, 'statsComparacion', 'subVistaStats == 2', editor_y=2200)
    label(s2, 'tituloPareadosUI', 28, 292, 'Comparar los tres escenarios', 18, INK)
    label(s2, 'textoGuiaEstudio', 28, 330,
          'Cargar resultados muestra el último estudio completo guardado.\n'
          'Para uno nuevo, abrí Comparacion_100x3; si guardaste cambios, elegí Usar guardados y ejecutar.',
          13, MUTED)
    button(s2, 'estudioUI', 28, 382, 350, 36, 'Guardar ajustes para el estudio', 'ejecutarComparacion();')
    button(s2, 'detenerEstudioUI', 394, 382, 266, 36, 'Cargar resultados', 'cargarUltimosIC();')
    label(s2, 'estadoEstudioUI', 690, 392, 'Estado', 13, MUTED,
          expr='SesionEstudio.ultimoResultado == null ? "Sin resultados cargados" : "Estudio completo · 100 pares por comparación"')
    for j, (title, metric) in enumerate([('Demanda atendida', 0), ('Pedidos pendientes', 1), ('Efecto látigo', 2)]):
        bx = 28 + j * 244
        button(s2, f'metricaIC{j}', bx, 454, 228, 34, title, f'metricaIC={metric};')
        mbar = panel(s2, f'metricaICBar{j}', bx, 492, 228, 3, TEAL)
        code(mbar, 'VisibleCode', f'metricaIC == {metric}')
    label(s2, 'metricaComparacionUI', 28, 520, 'Métrica', 17, INK, expr='tituloComparacionIC()')
    label(s2, 'sentidoComparacionUI', 28, 554, 'Cómo leer', 13, MUTED, expr='sentidoComparacionIC()')
    panel(s2, 'cabeceraTablaIC', 28, 596, 1224, 34, BG)
    for col, (title, x) in enumerate([('Escenarios (A − B)',44), ('Diferencia media',390), ('Intervalo del 95%',650), ('Lectura',960)]):
        label(s2, 'cabeceraIC'+str(col), x, 604, title, 14, INK)
    for row, y in enumerate([642, 710, 778]):
        panel(s2, 'lineaIC'+str(row), 28, y+57, 1224, 1, BORDER)
        for col, x in enumerate([44,390,650,960]):
            label(s2, 'celdaIC'+str(row)+str(col), x, y+8, '—', 16 if col==0 else 14,
                  INK if col<3 else TEAL, expr=f'celdaComparacionIC({row},{col})')
    label(s2, 'notaLecturaIC', 28, 858,
          'Si el intervalo incluye 0, no hay diferencia estadística clara. Una diferencia detectable puede ser pequeña.',
          13, MUTED)
    label(s2, 'rutaCSVLabel', 28, 904, 'Carpeta de resultados', 13, INK)
    edit(s2, 'campoCarpeta', 28, 930, 1224, 'carpetaResultados')

    # ------------------------------------------------------------------
    # Tab 3: Configuracion (Sub-tabs: Politica | Demanda | Planta)
    # ------------------------------------------------------------------
    v3 = group(scene, 'cuerpoVista3', 'vistaActiva == 3', editor_x=4200)
    label(v3, 'tituloConfigUI', 28, 184, 'Configuración', 18, INK)
    for i, (ctrl_name, title, x, w) in enumerate([
        ('subTabCfg0', 'Escenarios', 260, 200),
        ('subTabCfg1', 'Demanda', 474, 200),
        ('subTabCfg2', 'Planta', 688, 200),
    ]):
        x -= 232
        button(v3, ctrl_name, x, 222, w, 34, title, f'subVistaConfig={i};')
        bar = panel(v3, f'subTabCfgBar{i}', x, 260, w, 3, TEAL)
        code(bar, 'VisibleCode', f'subVistaConfig == {i}')
    panel(v3, 'lineaCfgHeader', 28, 272, 1224, 1, BORDER)

    # Sub-tab 3.0: Escenario y Politica
    c0 = group(v3, 'cfgPolitica', 'subVistaConfig == 0')
    panel(c0, 'card_escenarios_cfg', 40, 204, 560, 600, BG)
    label(c0, 'tituloEscenarios', 60, 228, 'Elegí una política', 17, INK)
    label(c0, 'notaEscenariosUI', 60, 264, 'Los tres escenarios mantienen la planta abierta 24×7.', 13, MUTED)
    scenarios_ui = [
        ('0 · Base', 'Amplifica las compras ante faltantes (α = 1,5).'),
        ('1 · Sin pánico', 'Repone sin amplificar las compras (α = 1).'),
        ('2 · Mejora integral', 'Sin pánico y 27,5% más cajas por hora.\nEs una mejora de rendimiento supuesta;\nla planta sigue abierta 24×7.'),
    ]
    for i, (title, desc) in enumerate(scenarios_ui):
        sy = 320 + i * 126
        button(c0, f'escenarioUI{i}', 60, sy, 510, 36, title, f'elegirEscenario({i});')
        sbar = panel(c0, f'escenarioBar{i}', 60, sy + 39, 510, 3, ACCENT)
        code(sbar, 'VisibleCode', f'escenarioActivo == {i}')
        label(c0, f'escenarioDesc{i}', 60, sy + 56, desc, 13, MUTED)
    label(c0, 'escenarioResumenCfgUI', 60, 744, 'Escenario', 13, TEAL,
          expr='"Activo: " + escenarioTexto()')

    panel(c0, 'card_politica_cfg', 624, 204, 612, 600, BG)
    label(c0, 'tituloPoliticaUI', 646, 228, 'Ajustes de la política', 17, INK)
    labeled_edit(c0, 'campoLatigoLabel', 'campoLatigo', 646, 282, 566, 'Amplificación de compras (α)', 'uiLatigo')
    label(c0, 'latigoAyudaUI', 646, 346, '1 = sin amplificación; valores mayores aumentan las compras.', 12, MUTED)
    labeled_edit(c0, 'esperaLabel', 'campoEspera', 646, 390, 566, 'Espera antes de cancelar un pedido (días)', 'uiEspera')
    labeled_edit(c0, 'maxWipLabel', 'campoMaxWip', 646, 476, 566, 'Máximo de lotes en proceso (1 lote = 1.000 cajas)', 'uiMaxWip')
    labeled_edit(c0, 'campoWarmupLabel', 'campoWarmup', 646, 562, 566, 'Calentamiento: semanas iniciales excluidas', 'uiWarmup')
    label(c0, 'warmupAyudaUI', 646, 626, 'Excluidas de servicio, producción y efecto látigo; la planta sigue operando.', 12, MUTED)
    button(c0, 'aplicarPoliticaUI', 646, 688, 566, 36, 'Aplicar ajustes', 'guardarPlanta();')
    label(c0, 'notaPoliticaUI', 646, 748,
          'La espera de 30 días y el límite de 36 lotes son supuestos.\nEl límite no puede ser menor que los lotes ya presentes.',
          12, MUTED)
    label(c0, 'notaAplicacionUI', 40, 848,
          'Los cambios rigen para los próximos pedidos y procesos. Los lotes iniciados conservan sus tiempos.',
          13, MUTED)

    # Sub-tab 3.1: Demanda por Perfil
    c1 = group(v3, 'cfgDemanda', 'subVistaConfig == 1', editor_y=1100)
    panel(c1, 'card_demanda', 40, 204, 560, 650, BG)
    label(c1, 'tituloDemandaUI', 60, 228, 'Elegí qué demanda modificar', 17, INK)
    label(c1, 'subtituloCanalUI', 60, 280, 'Canal comercial', 13, MUTED)
    for c, title in enumerate(['Maxiconsumo', 'Grandes clientes', 'Red propia']):
        cx = 60 + c * 176
        button(c1, f'canalUI{c}', cx, 308, 166, 34, title, f'seleccionarPerfil({c},perfilProducto);')
        cbar = panel(c1, f'canalBar{c}', cx, 346, 166, 3, TEAL)
        code(cbar, 'VisibleCode', f'perfilCanal == {c}')

    label(c1, 'subtituloProdUI', 60, 388, 'Producto', 13, MUTED)
    products = ['Lavandina', 'Desinfectante', 'Lavavajilla', 'Lavarropa', 'Suavizante', 'Detergente']
    for p, title in enumerate(products):
        px = 60 + (p % 2) * 260
        py = 418 + (p // 2) * 54
        button(c1, f'productoUI{p}', px, py, 248, 34, title, f'seleccionarPerfil(perfilCanal,{p});')
        pbar = panel(c1, f'productoBar{p}', px, py + 36, 248, 3, TEAL)
        code(pbar, 'VisibleCode', f'perfilProducto == {p}')

    label(c1, 'perfilFormUI', 60, 600, 'Perfil', 14, TEAL, expr='"Seleccionado: " + perfilTexto()')
    label(c1, 'notaDemandaUI', 60, 660,
          'Base: pedidos mensuales de 2025.\nSe sortean meses con reposición y se convierten\na demanda semanal, compartida entre escenarios.\n\n'
          'La variación es entre meses; no representa picos diarios.',
          13, MUTED)

    panel(c1, 'card_demanda_valores', 624, 204, 612, 650, BG)
    label(c1, 'tituloDemandaValoresUI', 646, 228, 'Valores del perfil seleccionado', 17, INK)
    labeled_edit(c1, 'mediaLabel', 'campoMedia', 646, 304, 566, 'Media (cajas / semana)', 'uiMedia')
    label(c1, 'mediaAyudaUI', 646, 370, 'Cantidad promedio pedida por este canal y producto.', 13, MUTED)
    labeled_edit(c1, 'sdLabel', 'campoDesvio', 646, 430, 566, 'Desvío estándar (cajas / semana)', 'uiDesvio')
    label(c1, 'desvioAyudaUI', 646, 496,
          'Mide cuánto cambia el perfil mensual.\nUn valor mayor genera más variación respecto de la media.', 13, MUTED)
    button(c1, 'aplicarDemandaUI', 646, 586, 566, 36, 'Aplicar al perfil seleccionado', 'guardarDemanda();')

    # Sub-tab 3.2: Planta y Capacidad
    c2 = group(v3, 'cfgPlanta', 'subVistaConfig == 2', editor_y=2200)
    panel(c2, 'card_inventario', 40, 204, 586, 650, BG)
    label(c2, 'tituloInventarioUI', 60, 228, 'Inventario y capacidad', 17, INK)
    for p, title in enumerate(products):
        px = 60 + (p % 3) * 184
        py = 270 + (p // 3) * 50
        button(c2, f'productoCfgUI{p}', px, py, 176, 28, title, f'seleccionarPerfil(perfilCanal,{p});')
        pbar = panel(c2, f'productoCfgBar{p}', px, py + 36, 176, 3, TEAL)
        code(pbar, 'VisibleCode', f'perfilProducto == {p}')
    label(c2, 'perfilPlantaUI', 60, 374, 'Producto', 13, TEAL,
          expr='"Producto seleccionado: " + nombreProducto(perfilProducto)')

    for j, (lab, name, link) in enumerate([
        ('Apertura de la planta (horas / semana; máximo 168)', 'campoHoras', 'uiHoras'),
        ('Plazo de entrega del proveedor (días, por producto)', 'campoLead', 'uiLead'),
        ('Stock objetivo (semanas de demanda, por producto)', 'campoCobertura', 'uiCobertura'),
        ('Ritmo de envasado (cajas / hora abierta, por producto)', 'campoRate', 'uiRate'),
        ('Multiplicador de rendimiento (1 = base)', 'campoCapacidad', 'uiCapacidad'),
    ]):
        labeled_edit(c2, name + 'Label', name, 60, 412 + j * 86, 546, lab, link)

    panel(c2, 'card_proceso', 650, 204, 586, 650, BG)
    label(c2, 'tituloProcesoUI', 670, 228, 'Ajustes del proceso', 17, INK)
    for j, (lab, label_name, name, link) in enumerate([
        ('Rechazo adicional de lavandina (%)', 'campoMermaLavLabel', 'campoMermaLav', 'uiMermaLav'),
        ('Rechazo adicional de líquidos (%)', 'campoMermaLiqLabel', 'campoMermaLiq', 'uiMermaLiq'),
        ('Multiplicador de duración (1 = base; mayor = más lento)', 'campoTiempoLabel', 'campoTiempo', 'uiTiempo'),
        ('Reactores en paralelo', 'campoReactoresLabel', 'campoReactores', 'uiReactores'),
        ('Espacio en la cola de elaboración (lotes)', 'campoColaLabel', 'campoCola', 'uiCola'),
        ('Espacio en cada tanque (lotes)', 'tanqueLabel', 'campoTanque', 'uiTanque'),
    ]):
        labeled_edit(c2, label_name, name, 670, 282 + j * 86, 546, lab, link)

    button(c2, 'aplicarPlantaUI', 40, 874, 1196, 36, 'Aplicar cambios de planta', 'guardarPlanta();')
    label(c2, 'notaAjustesPlantaUI', 40, 930,
          'Los rechazos son adicionales al rendimiento histórico. Apertura, multiplicadores y recursos rigen para toda la planta.', 12, MUTED)

    # A separate row for each navigation level; content starts below all headers.
    # Compress only vertical spacing, preserving font and control sizes.
    for content in [s0, s1, c0, c1, c2]:
        for n in children(content):
            if children(n, 'Y'):
                put(n, 'Y', 292 + (float(text(n, 'Y')) - 204) * .88)
            if n.tagName in ['Rectangle', 'TimePlot']:
                put(n, 'Height', float(text(n, 'Height')) * .88)
            if n.tagName == 'TimePlot':
                chart = children(n, 'ChartArea')[0]
                for tag in ['YOffset', 'Height']:
                    put(chart, tag, float(text(chart, tag)) * .88)
    for bar_prefix, control_prefix, count in [
        ('escenarioBar','escenarioUI',3), ('canalBar','canalUI',3),
        ('productoBar','productoUI',6), ('productoCfgBar','productoCfgUI',6),
    ]:
        for i in range(count):
            bar, control = byname(bar_prefix+str(i)), byname(control_prefix+str(i))
            height = float(children(control,'BasicProperties')[0].getAttribute('Height'))
            put(bar, 'Y', float(text(control,'Y')) + height + 3)

    # 3D camera + quiet footer message
    camera = fresh(tpl_camera)
    import math
    for k, v in {'X':920, 'Y':605+1100/math.tan(math.radians(55)), 'Z':1100, 'RotationX':55, 'RotationZ':-90}.items():
        put(camera,k,v)
    scene.appendChild(camera)
    message = label(scene, 'mensajeUItexto', 24, 986, 'Mensaje', 11, MUTED, expr='mensajeUI')
    code(message, 'VisibleCode', 'vistaActiva != 0')

    # Update Main AdditionalClassCode cleanly, keeping GUIA_PLANTA helpers.
    additional = _strip_var_decls((ROOT / 'tools/MainInterfaz.code.java.txt').read_text(encoding='utf8'))
    code(main, 'AdditionalClassCode', additional + _guia_planta_java(sectors))

    # Fix invalid RunConfigurationOutput names copied from old chart captions.
    for rco in model.getElementsByTagName('RunConfigurationOutput'):
        name = text(rco, 'Name')
        if '|' in name or name.startswith('ESTADISTICAS'):
            put(rco, 'Name', 'Plot demanda y ordenes')

    # Keep the study's return instruction aligned with the renamed UI action.
    for experiment in children(children(model, 'Experiments')[0]):
        if text(experiment, 'Name') == 'Comparacion_100x3':
            for n in experiment.getElementsByTagName('Text'):
                value = text(n, 'Text')
                renamed = value.replace('Main > Estadisticas > Leer ultimos IC',
                    'Main > Estadísticas > Comparar escenarios > Cargar resultados')
                renamed = renamed.replace('Cargar últimos resultados', 'Cargar resultados')
                if renamed != value:
                    put(n, 'Text', renamed)

    # Preserve identities used by the IDE and existing model outputs.
    for n in scene.getElementsByTagName('*'):
        if text(n, 'Name') in original_ids and children(n, 'Id'):
            put(n, 'Id', original_ids[text(n, 'Name')])


def main():
    backup = Path(tempfile.mkdtemp(prefix='domitec-antes-modularizar-'))
    paths = [ALP]
    autosave = ALP.with_suffix('.alp.autosave')
    if autosave.exists():
        paths.append(autosave)
    # Capture both versions first. Never replace the newer editor recovery
    # version with the older saved model; transform each version independently.
    originals = {p: p.read_bytes() for p in paths}
    for p, contents in originals.items():
        (backup / p.name).write_bytes(contents)
    updated = {}
    for p, contents in originals.items():
        d = D.parseString(contents)
        modularizar(d)
        updated[p] = d.toxml(encoding='UTF-8')
    if any(p.read_bytes() != originals[p] for p in paths):
        raise RuntimeError('El modelo cambió durante la preparación; no se escribió ningún archivo.')
    for p, contents in updated.items():
        p.write_bytes(contents)
        print('Updated', p)
    print('Backup:', backup)


if __name__ == '__main__':
    main()
