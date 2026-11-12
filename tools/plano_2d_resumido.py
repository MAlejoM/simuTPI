"""Simplified native 2D production flow with live process counters."""


def crear_plano_resumido(parent, panel, label):
    """Draw uncluttered production flows and live inventory figures in Main."""
    ink = -15193551
    muted = -9603453
    border = -1906964
    white = -1
    park = -15238159
    teal = -14381747
    pale = -14013155

    # Neutral drawing area; the screen header is owned by Main.
    panel(parent, "planoFondo", 24, 200, 1232, 760, white, border)

    label(parent, "planoParqueTitulo", 48, 226, "PARQUE | LAVANDINA", 22, park)
    stages = [
        ("Recepcion", "Recepción", 0),
        ("Dilucion", "Dilución", 1),
        ("Calidad", "Control de calidad", 2),
        ("Pulmon", "Pulmón", 3),
        ("Envasado", "Envasado", 4),
    ]
    xs = (60, 300, 540, 780, 1020)
    for i, (key, title, stage) in enumerate(stages):
        x = xs[i]
        label(parent, f"planoParque{key}Titulo", x, 280, title, 18, ink)
        label(parent, f"planoParque{key}Count", x, 325, "0 lotes", 28, park,
              expr=f'numero(lotesEtapa(0,{stage})) + " lotes"')
        if i < len(stages) - 1:
            label(parent, f"planoParqueFlecha{i}", x + 200, 318, "→", 24, muted)
    label(parent, "planoParqueStock", 60, 390, "Stock: 0 cajas", 22, ink,
          expr='"Stock: " + numero(stockProducto(0)) + " cajas"')
    label(parent, "planoParqueBacklog", 540, 390, "Pendientes: 0 cajas", 22, muted,
          expr='"Pendientes: " + numero(backlogProducto(0)) + " cajas"')

    panel(parent, "planoSeparador", 48, 440, 1184, 2, pale)
    label(parent, "planoVicentinTitulo", 48, 465, "VICENTIN | LÍQUIDOS FORMULADOS", 22, teal)

    shared = [
        ("Recepcion", "Recepción", 60, 0),
        ("Reactores", "Reactores / proceso", 460, 1),
        ("Calidad", "Control de calidad", 860, 2),
    ]
    for key, title, x, stage in shared:
        label(parent, f"planoVicentin{key}Titulo", x, 518, title, 18, ink)
        if stage == 0:
            expr = '"En espera: " + numero(lotesEtapa(1,0)+lotesEtapa(2,0)+lotesEtapa(3,0)+lotesEtapa(4,0)+lotesEtapa(5,0)) + " lotes"'
        elif stage == 1:
            expr = '"En proceso: " + numero(lotesEtapa(1,1)+lotesEtapa(2,1)+lotesEtapa(3,1)+lotesEtapa(4,1)+lotesEtapa(5,1)) + " lotes"'
        else:
            expr = '"En control: " + numero(lotesEtapa(1,2)+lotesEtapa(2,2)+lotesEtapa(3,2)+lotesEtapa(4,2)+lotesEtapa(5,2)) + " lotes"'
        label(parent, f"planoVicentin{key}Count", x, 555, "0 lotes", 24, teal, expr=expr)
    label(parent, "planoVicentinFlecha0", 390, 548, "→", 24, muted)
    label(parent, "planoVicentinFlecha1", 790, 548, "→", 24, muted)

    # Per-product table. Stage counts and inventory totals are shown once.
    label(parent, "planoTablaCabeceraProducto", 60, 622, "Producto", 18, muted)
    label(parent, "planoTablaCabeceraPulmon", 340, 622, "Pulmón", 18, muted)
    label(parent, "planoTablaCabeceraEnvasado", 540, 622, "Envasado", 18, muted)
    label(parent, "planoTablaCabeceraStock", 760, 622, "Stock", 18, muted)
    label(parent, "planoTablaCabeceraPendientes", 990, 622, "Pendientes", 18, muted)

    products = ("Desinfectante", "Lavavajilla", "Lavarropa", "Suavizante", "Detergente")
    row_y = (674, 718, 762, 806, 850)
    for row, (product, yy) in enumerate(zip(products, row_y)):
        index = row + 1
        label(parent, f"planoTablaProducto{row}", 60, yy, product, 20, ink)
        label(parent, f"planoTablaPulmon{row}", 340, yy, "0 lotes", 20, ink,
              expr=f'numero(lotesEtapa({index},3)) + " lotes"')
        label(parent, f"planoTablaEnvasado{row}", 540, yy, "0 lotes", 20, ink,
              expr=f'numero(lotesEtapa({index},4)) + " lotes"')
        label(parent, f"planoTablaStock{row}", 760, yy, "0 cajas", 20, ink,
              expr=f'numero(stockProducto({index})) + " cajas"')
        label(parent, f"planoTablaPendientes{row}", 990, yy, "0 cajas", 20, ink,
              expr=f'numero(backlogProducto({index})) + " cajas"')

    label(parent, "planoNota", 60, 924,
          "Pulmón: producto semielaborado antes del envasado. Cada lote = 1.000 cajas.", 16, muted)
