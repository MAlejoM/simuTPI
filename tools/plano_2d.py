"""Author the clean, native 2D plant status view in Main."""


def crear_plano(g, panel, label):
    """Add a six-product flow board using the Main XML authoring callbacks."""
    # AnyLogic color integers, matching the rest of the interactive Main UI.
    colors = {
        "ink": -15193551,
        "teal": -14381747,
        "background": -658189,
        "card": -1,
        "border": -1906964,
        "muted": -9603453,
        "park": -15238159,
        "vicentin": -11546643,
    }

    panel(g, "planoFondo", 24, 200, 1232, 698, colors["background"], colors["border"])
    label(g, "planoTitulo", 40, 231, "FLUJO DE LOTES | PARQUE Y VICENTIN", 14, colors["teal"])

    columns = [
        (40, 164, "PRODUCTO / SECTOR"),
        (212, 140, "RECEPCION"),
        (360, 140, "ELABORACION"),
        (508, 140, "CALIDAD"),
        (656, 140, "TANQUE"),
        (804, 140, "ENVASADO"),
        (952, 284, "STOCK / BACKLOG"),
    ]
    for i, (x, width, title) in enumerate(columns):
        panel(g, f"planoCabecera{i}", x, 253, width, 34, colors["ink"])
        label(g, f"planoCabeceraTexto{i}", x + 8, 262, title, 12, -1)

    products = [
        ("Lavandina", "PARQUE", 0),
        ("Desinfectante", "VICENTIN", 1),
        ("Lavavajilla", "VICENTIN", 2),
        ("Lavarropa", "VICENTIN", 3),
        ("Suavizante", "VICENTIN", 4),
        ("Detergente", "VICENTIN", 5),
    ]
    stages = [
        ("recepcion", 0),
        ("proceso", 1),
        ("qc", 2),
        ("tanque", 3),
        ("envasado", 4),
    ]
    for row, (product, sector, index) in enumerate(products):
        y = 296 + row * 80
        sector_color = colors["park"] if sector == "PARQUE" else colors["vicentin"]
        panel(g, f"planoFila{row}", 40, y, 1196, 72, colors["card"], colors["border"])
        panel(g, f"planoSector{row}", 40, y, 6, 72, sector_color)
        label(g, f"planoProducto{row}", 54, y + 25, product, 12, colors["ink"])
        label(g, f"planoSectorTexto{row}", 54, y + 49, sector, 10, colors["muted"])

        for col, (stage_name, stage) in enumerate(stages, start=1):
            x = columns[col][0] + 8
            label(
                g,
                f"planoLote{row}_{stage_name}",
                x,
                y + 41,
                "Lotes",
                12,
                colors["ink"],
                expr=f'"Lotes: " + lotesEtapa({index},{stage})',
            )

        stock_x = columns[6][0] + 8
        label(
            g,
            f"planoStock{row}",
            stock_x,
            y + 29,
            "Stock",
            12,
            colors["ink"],
            expr=f'"Stock: " + String.format(java.util.Locale.ROOT,"%.0f",stockProducto({index})) + " cajas"',
        )
        label(
            g,
            f"planoBacklog{row}",
            stock_x,
            y + 53,
            "Backlog",
            12,
            colors["muted"],
            expr=f'"Backlog: " + String.format(java.util.Locale.ROOT,"%.0f",backlogProducto({index})) + " cajas"',
        )

    label(g, "planoNota", 40, 858, "Cada lote representa 1.000 cajas. Los indicadores se actualizan durante la simulacion.", 11, colors["muted"])
