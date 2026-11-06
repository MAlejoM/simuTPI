"""Author a clear, native 2D industrial flow plan in Main."""


def crear_plano(g, panel, label):
    """Draw the Parque and Vicentin process areas with live lot indicators."""
    ink = -15193551
    muted = -9603453
    border = -1906964
    background = -658189
    white = -1
    park = -15238159
    vicentin = -11546643
    teal = -14381747
    pale_teal = -14013155

    panel(g, "planoFondo", 24, 200, 1232, 698, background, border)
    label(g, "planoTitulo", 48, 222, "PLANTA DE PRODUCCION | FLUJO DE LOTES", 16, ink)
    label(g, "planoParqueTitulo", 55, 256, "PARQUE | LAVANDINA", 16, park)
    label(g, "planoVicentinTitulo", 55, 520, "VICENTIN | LIQUIDOS FORMULADOS", 16, teal)

    def card(name, x, y, w, h, title, color):
        panel(g, f"plano{ name }", x, y, w, h, white, border)
        panel(g, f"plano{ name }Franja", x, y, w, 28, color)
        label(g, f"plano{ name }Titulo", x + 10, y + 7, title, 13, ink if color==vicentin else white)

    def arrow(name, x, y, width=22):
        label(g,f"plano{name}Flecha",x,y-4,"→",16,teal)

    def tank(name,x,y):
        panel(g,f"plano{name}Tanque",x,y,40,43,-3810857,border)
        panel(g,f"plano{name}Tapa",x-2,y,44,6,teal)
        panel(g,f"plano{name}Pie",x+7,y+43,26,5,ink)

    def count(name, x, y, product_index, stage, color=ink):
        label(
            g, name, x, y, "Lotes: 0", 13, color,
            expr=f'"Lotes: " + numero(lotesEtapa({product_index},{stage}))',
        )

    # Parque: receipt -> dilution/QC -> filling -> storage.
    card("ParqueRecepcion", 55, 280, 205, 190, "1. RECEPCION", park)
    card("ParqueDilucion", 275, 280, 235, 190, "2. DILUCION / QC", park)
    card("ParqueEnvasado", 525, 280, 435, 190, "3. ENVASADO", park)
    card("ParqueDeposito", 975, 280, 245, 190, "4. DEPOSITO / CAJAS", park)
    label(g, "planoParqueMateria", 68, 325, "Lavandina", 13, ink)
    tank('Hipo',88,352);tank('Insumos',178,352)
    label(g, "planoParqueRecepDesc", 68, 412, "Ingreso y preparacion", 13, muted)
    count("planoParqueCola", 68, 439, 0, 0)
    label(g, "planoParqueDilucionDesc", 288, 325, "Dilucion y control de calidad", 13, ink)
    label(g,"planoParqueProceso",288,374,"Dilucion: 0",13,ink,expr='"Dilucion: " + numero(lotesEtapa(0,1)) + " lotes"')
    label(g,"planoParqueQc",288,401,"QC: 0",13,ink,expr='"QC: " + numero(lotesEtapa(0,2)) + " lotes"')
    label(g,"planoParquePulmon",288,428,"Pulmon: 0",13,ink,expr='"Pulmon: " + numero(lotesEtapa(0,3)) + " lotes"')
    label(g, "planoParqueLinea", 540, 325, "Linea de envasado", 13, ink)
    panel(g,'planoCintaParque',540,391,400,7,muted)
    for stage in range(6):
        x=551+64*stage
        panel(g,f'planoEquipoParque{stage}',x,353,44,34,-3810857,border)
        panel(g,f'planoEquipoParqueTapa{stage}',x,353,44,5,teal)
        label(g,f'planoEquipoParqueNombre{stage}',x+12,366,'E'+str(stage+1),11,ink)
    label(g,'planoPasosParque',540,409,'Envases → llenado → cierre → cajas',12,muted)
    label(g,'planoParqueEnvasadoCount',540,437,'Envasado: 0',13,ink,expr='"Envasado: " + numero(lotesEtapa(0,4)) + " lotes"')
    label(g, "planoParqueStock", 990, 411, "Stock: 0 cajas", 13, ink,
          expr='"Stock: " + numero(stockProducto(0)) + " cajas"')
    label(g, "planoParqueBacklog", 990, 439, "Backlog: 0 cajas", 13, muted,
          expr='"Backlog: " + numero(backlogProducto(0)) + " cajas"')
    label(g, "planoParqueDepositoDesc", 990, 325, "Producto terminado", 13, ink)
    label(g, "planoParqueDepositoNote", 990, 350, "Almacen y despacho", 13, muted)
    for j in range(3):
        panel(g,f'planoPalletParque{j}',993+j*68,377,43,22,-3355546,border)
        panel(g,f'planoPalletBaseParque{j}',990+j*68,399,49,4,muted)
    arrow("ParqueFlujo1", 261, 365)
    arrow("ParqueFlujo2", 511, 365)
    arrow("ParqueFlujo3", 961, 365)

    # Vicentin: one shared reactor/QC and buffer path feeding five product lines.
    card("VicentinRecepcion", 55, 550, 205, 275, "5. RECEPCION", vicentin)
    card("VicentinQc", 275, 550, 235, 120, "6. REACTORES / QC", vicentin)
    card("VicentinPulmon", 275, 685, 235, 140, "7. TANQUES PULMON", vicentin)
    card("VicentinEnvasado", 525, 550, 435, 275, "8. ENVASADO", vicentin)
    card("VicentinDeposito", 975, 550, 245, 275, "9. DEPOSITO / CAJAS", vicentin)
    label(g, "planoVicentinRecepDesc", 68, 600, "Recepcion de insumos", 13, ink)
    label(g, "planoVicentinRecepHint", 68, 626, "Preparacion de lotes", 13, muted)
    tank('BaseLiquidos',88,668);tank('InsumosLiquidos',178,668)
    label(g,'planoVicentinMateriales',68,737,'Bases, esencias y envases',12,muted)
    label(g,'planoVicentinCola',68,773,'En espera: 0',13,ink,expr='"En espera: " + numero(lotesEtapa(1,0)+lotesEtapa(2,0)+lotesEtapa(3,0)+lotesEtapa(4,0)+lotesEtapa(5,0)) + " lotes"')
    label(g, "planoVicentinQcDesc", 288, 593, "Reactores: 0", 13, ink,expr='"Reactores disponibles: " + numero(cfg.reactores)')
    label(g, "planoVicentinProcesoCount", 288, 626, "Proceso: 0", 13, muted,
          expr='"Proceso: " + numero(lotesEtapa(1,1)+lotesEtapa(2,1)+lotesEtapa(3,1)+lotesEtapa(4,1)+lotesEtapa(5,1))')
    label(g, "planoVicentinQcCount", 288, 648, "QC: 0", 13, muted,
          expr='"QC: " + numero(lotesEtapa(1,2)+lotesEtapa(2,2)+lotesEtapa(3,2)+lotesEtapa(4,2)+lotesEtapa(5,2))')
    for row,short in enumerate(['Desinf.','Lavavaj.','Lavarropa','Suaviz.','Deterg.']):
        label(g,f'planoPulmonLinea{row}',288,719+row*19,'Lotes',12,ink,expr=f'"{short}: " + numero(lotesEtapa({row+1},3)) + " lotes"')
    panel(g,'planoBajadaPulmon',390,672,2,11,teal)

    products = ["Lavandina", "Desinfectante", "Lavavajilla", "Lavarropa", "Suavizante", "Detergente"]
    for row, (name, index) in enumerate(zip(products[1:], range(1, 6))):
        yy = 589 + row * 38
        panel(g, f"planoLinea{row}", 538, yy - 5, 409, 33, background, border)
        panel(g, f"planoLinea{row}Indicador", 538, yy - 5, 5, 33, pale_teal)
        label(g, f"planoLinea{row}Nombre", 551, yy, name, 13, ink)
        panel(g,f'planoCintaLiquido{row}',660,yy+14,155,3,muted)
        for stage in range(6):
            x=663+25*stage
            panel(g,f'planoEquipoLiquido{row}_{stage}',x,yy+1,20,18,-3810857,border)
            label(g,f'planoEtapaLiquido{row}_{stage}',x+6,yy+5,str(stage+1),9,ink)
        label(g, f"planoLinea{row}Lotes", 832, yy, "0 lotes", 13, muted,
              expr=f'numero(lotesEtapa({index},4)) + " lotes"')
        label(g,f'planoDepositoProducto{row}',990,yy,name,12,ink)
        label(g,f'planoDepositoStock{row}',1100,yy,'0',13,ink,expr=f'numero(stockProducto({index}))')
    label(g,'planoVicentinPasos',540,790,'Envases → llenado → cierre → cajas',12,muted)
    label(g, "planoVicentinStock", 990, 790, "Total: 0 cajas", 12, ink,
          expr='"Total: " + numero(stockProducto(1)+stockProducto(2)+stockProducto(3)+stockProducto(4)+stockProducto(5)) + " cajas"')
    label(g, "planoVicentinBacklog", 990, 808, "Backlog: 0 cajas", 11, muted,
          expr='"Backlog: " + numero(backlogProducto(1)+backlogProducto(2)+backlogProducto(3)+backlogProducto(4)+backlogProducto(5)) + " cajas"')
    arrow("VicentinFlujo1", 261, 682)
    arrow("VicentinFlujo2", 511, 682)
    arrow("VicentinFlujo3", 961, 682)

    label(g, "planoNota", 55, 858, "Plano esquematico | Cada lote = 1.000 cajas | Datos en vivo del proceso.", 13, muted)
