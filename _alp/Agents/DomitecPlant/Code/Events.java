void planificacionSemanal()
{/*ALCODESTART::1788973656817*/
traceln("=== 📊 REVISIÓN SEMANAL DE PRODUCCIÓN Y COMPRAS ===");

double reqCajas = 0;
double reqPreformas = 0;
double reqPE = 0;
double reqFilm = 0;
double reqEtiquetas = 0;
double reqBase = 0;
double reqTenso = 0;
double reqEsencia = 0;

double totalOrdenesSemana = 0;

for (ProductState ps : inventorySystem) {
    
    // 1. COBERTURA SEGÚN LEAD TIME DEL PROVEEDOR
    double semanasCobertura = 4.0;
    if (ps.product == ProductType.LAVANDINA) {
        semanasCobertura = 5.5;    // LT 4.3 sem + margen
    } else if (ps.product == ProductType.SUAVIZANTE) {
        semanasCobertura = 7.5;    // LT 6.4 sem + margen
    } else if (ps.product == ProductType.LIQUIDO_DESINFECTANTE) {
        semanasCobertura = 4.5;    // LT 3.0 sem + margen
    } else if (ps.product == ProductType.LAVAVAJILLA) {
        semanasCobertura = 4.0;    // LT 3.0 sem + margen
    } else if (ps.product == ProductType.LIQUIDO_LAVAR_ROPA) {
        semanasCobertura = 4.0;    // LT 3.0 sem + margen
    } else if (ps.product == ProductType.DETERGENTE_CONCENTRADO) {
        semanasCobertura = 4.0;    // LT 3.0 sem + margen
    }
    
    double targetStock = ps.weeklyCapacity * semanasCobertura;
    
    // 2. CÁLCULO EXACTO DEL WIP FÍSICO REAL POR PRODUCTO (SIN DIVIDIR POR 5)
    double wipReal = 0;
    if (ps.product == ProductType.LAVANDINA) {
        wipReal = (queueMateriaPrima.size() 
                  + delayDilucion.size() 
                  + delayQCLavandina.size() 
                  + queueTanquePulmon.size() 
                  + delayEnvasado.size()) * 1000.0;
    } else {
        int lotesComunes = 0;
        for (int i = 0; i < queueEsperaElaboracion.size(); i++) {
            if (((Batch)queueEsperaElaboracion.get(i)).tipo == ps.product) lotesComunes++;
        }
        for (int i = 0; i < delayReactoresLiquidos.size(); i++) {
            if (((Batch)delayReactoresLiquidos.get(i)).tipo == ps.product) lotesComunes++;
        }
        for (int i = 0; i < delayQCLiquidos.size(); i++) {
            if (((Batch)delayQCLiquidos.get(i)).tipo == ps.product) lotesComunes++;
        }
        
        int lotesLinea = 0;
        if (ps.product == ProductType.LAVAVAJILLA) {
            lotesLinea = tankLavavajilla.size() + delayEnvasadoLavavajilla.size();
        } else if (ps.product == ProductType.LIQUIDO_LAVAR_ROPA) {
            lotesLinea = tankLavarropa.size() + delayEnvasadoLavarropa.size();
        } else if (ps.product == ProductType.SUAVIZANTE) {
            lotesLinea = tankSuavizante.size() + delayEnvasadoSuavizante.size();
        } else if (ps.product == ProductType.DETERGENTE_CONCENTRADO) {
            lotesLinea = tankDetergente.size() + delayEnvasadoDetergente.size();
        } else if (ps.product == ProductType.LIQUIDO_DESINFECTANTE) {
            lotesLinea = tankDesinfectante.size() + delayEnvasadoDesinfectante.size();
        }
        wipReal = (lotesComunes + lotesLinea) * 1000.0;
    }
    
        // 3. POSICIÓN DE INVENTARIO NETA (Descontando el backlog de lo que ya tenemos o viene en viaje)
    double posicionNeta = (ps.inventory + ps.onOrder + wipReal) - ps.backlog;
    double faltanteNeto = Math.max(0, targetStock - posicionNeta);
    
    // Si hay deuda (backlog > 0), amplifica solo la parte del faltante sin volver a pedir lo que ya está en viaje:
    double aFabricar = faltanteNeto * (ps.backlog > 0 ? factorLatigo : 1.0);
    
    // Tope físico: no pedir en una sola semana más de 2 semanas de capacidad de máquina
    aFabricar = Math.min(aFabricar, ps.weeklyCapacity * 2.0);   
    // Redondeamos a múltiplos de 1.000 cajas (1 lote) para que no se pierdan remanentes al inyectar Batches
    long pedidoFinal = Math.round(aFabricar / 1000.0) * 1000L;
    
    if (pedidoFinal > 0) {
        ((Main)get_Main()).ordenesHistoricas += pedidoFinal;
        totalOrdenesSemana += pedidoFinal;
        
        // Se registra el insumo como pedido en tránsito
        ps.onOrder += pedidoFinal;
        
        // --- EXPLOSIÓN DE MATERIALES (BOM) ---
        reqCajas += pedidoFinal * 1; 
        
        if (ps.product == ProductType.LAVANDINA) {
            reqPE += pedidoFinal * 0.36; 
            reqEtiquetas += pedidoFinal * 12;
            reqBase += pedidoFinal * 12.18;
        }
        else if (ps.product == ProductType.LIQUIDO_DESINFECTANTE) {
            reqPreformas += pedidoFinal * 15;
            reqEtiquetas += pedidoFinal * 15;
            reqBase += pedidoFinal * 13.50;
            reqEsencia += pedidoFinal * 0.04;
        }
        else if (ps.product == ProductType.LAVAVAJILLA) {
            reqPreformas += pedidoFinal * 15;
            reqEtiquetas += pedidoFinal * 15;
            reqBase += pedidoFinal * 11.25;
            reqTenso += pedidoFinal * 1.0125;
            reqEsencia += pedidoFinal * 0.05;
        }
        else if (ps.product == ProductType.LIQUIDO_LAVAR_ROPA) {
            reqPreformas += pedidoFinal * 12;
            reqEtiquetas += pedidoFinal * 12;
            reqBase += pedidoFinal * 10.80;
            reqTenso += pedidoFinal * 0.864;
            reqEsencia += pedidoFinal * 0.08;
        }
        else if (ps.product == ProductType.SUAVIZANTE) {
            reqFilm += pedidoFinal * 0.014;
            reqBase += pedidoFinal * 14.11;
            reqTenso += pedidoFinal * 0.3456;
            reqEsencia += pedidoFinal * 0.08;
        }
        else if (ps.product == ProductType.DETERGENTE_CONCENTRADO) {
            reqPreformas += pedidoFinal * 15;
            reqEtiquetas += pedidoFinal * 15;
            reqBase += pedidoFinal * 5.25;
            reqTenso += pedidoFinal * 0.945;
            reqEsencia += pedidoFinal * 0.03;
        }
        
        send(new OrderMessage(ps.product, pedidoFinal), ((Main)get_Main()).supplier);
    }
}

// 4. REGISTRO EN DATASETS PARA LOS GRÁFICOS (1 muestra semanal)
Main m = (Main)get_Main();
m.ordenesSemanalActual = totalOrdenesSemana;

m.dsDemanda.add(time(), m.demandaSemanalActual);
m.dsOrdenes.add(time(), m.ordenesSemanalActual);

double totalBacklog = 0.0;
double totalStock = 0.0;
for (ProductState ps : inventorySystem) {
    totalBacklog += ps.backlog;
    totalStock += ps.inventory;
}

double totalWip = (queueMateriaPrima.size() 
                + delayDilucion.size() 
                + delayQCLavandina.size() 
                + queueTanquePulmon.size() 
                + delayEnvasado.size() 
                + queueEsperaElaboracion.size() 
                + delayReactoresLiquidos.size() 
                + delayQCLiquidos.size() 
                + tankLavavajilla.size() + delayEnvasadoLavavajilla.size() 
                + tankLavarropa.size() + delayEnvasadoLavarropa.size() 
                + tankSuavizante.size() + delayEnvasadoSuavizante.size() 
                + tankDetergente.size() + delayEnvasadoDetergente.size() 
                + tankDesinfectante.size() + delayEnvasadoDesinfectante.size()) * 1000.0;

m.dsBacklog.add(time(), totalBacklog);
m.dsWip.add(time(), totalWip);
m.dsProduccionSemanal.add(time(), m.produccionSemanalActual);

// Actualización dinámica de los indicadores en el plano visual de planta
double wipLav = (queueMateriaPrima.size() + delayDilucion.size() + delayQCLavandina.size() + queueTanquePulmon.size() + delayEnvasado.size()) * 1000.0;
double wipDes = (tankDesinfectante.size() + delayEnvasadoDesinfectante.size()) * 1000.0;
double wipLvj = (tankLavavajilla.size() + delayEnvasadoLavavajilla.size()) * 1000.0;
double wipLvr = (tankLavarropa.size() + delayEnvasadoLavarropa.size()) * 1000.0;
double wipSua = (tankSuavizante.size() + delayEnvasadoSuavizante.size()) * 1000.0;
double wipDet = (tankDetergente.size() + delayEnvasadoDetergente.size()) * 1000.0;

estado_lavandina.setText("Stock: " + Math.round(inventorySystem.get(0).inventory) + " | WIP: " + Math.round(wipLav) + " | Deuda: " + Math.round(inventorySystem.get(0).backlog));
estado_desinfectante.setText("Stock: " + Math.round(inventorySystem.get(1).inventory) + " | WIP: " + Math.round(wipDes) + " | Deuda: " + Math.round(inventorySystem.get(1).backlog));
estado_lavavajilla.setText("Stock: " + Math.round(inventorySystem.get(2).inventory) + " | WIP: " + Math.round(wipLvj) + " | Deuda: " + Math.round(inventorySystem.get(2).backlog));
estado_lavarropa.setText("Stock: " + Math.round(inventorySystem.get(3).inventory) + " | WIP: " + Math.round(wipLvr) + " | Deuda: " + Math.round(inventorySystem.get(3).backlog));
estado_suavizante.setText("Stock: " + Math.round(inventorySystem.get(4).inventory) + " | WIP: " + Math.round(wipSua) + " | Deuda: " + Math.round(inventorySystem.get(4).backlog));
estado_detergente.setText("Stock: " + Math.round(inventorySystem.get(5).inventory) + " | WIP: " + Math.round(wipDet) + " | Deuda: " + Math.round(inventorySystem.get(5).backlog));

// Reinicio de acumuladores de la semana
m.demandaSemanalActual = 0;
m.produccionSemanalActual = 0;

// === REPORTE RESUMEN FINAL AL TERMINAR LA CORRIDA ===
if (time() >= 99.0) {
    double fillRateGlobal = (demandaTotalAcumulada > 0) ? (despachoInmediatoAcumulado / demandaTotalAcumulada) * 100.0 : 0.0;
    traceln("====================================================================");
    traceln(">> RESULTADOS FINALES DE CORRIDA (Semana 100.0 - Fin de Simulacion):");
    traceln("   * Nivel de Servicio (Fill Rate): " + String.format("%.2f%%", fillRateGlobal));
    traceln("   * Demanda Total Acumulada:       " + Math.round(demandaTotalAcumulada) + " cajas");
    traceln("   * Despachado Inmediato:          " + Math.round(despachoInmediatoAcumulado) + " cajas");
    traceln("   * Backlog Residual en Planta:    " + Math.round(totalBacklog) + " cajas");
    traceln("   * Stock en Deposito:             " + Math.round(totalStock) + " cajas");
    traceln("   * WIP en Proceso Fabril:         " + Math.round(totalWip) + " cajas");
    traceln("   * Ordenes Historicas Emitidas:   " + Math.round(m.ordenesHistoricas) + " cajas");
    traceln("====================================================================");
}
/*ALCODEEND*/}

void avanceProduccion()
{/*ALCODESTART::1789240000002*/
// Un paso = 15 min. Turno supuesto: lunes a viernes de 08:00 a 16:00.
// Inicio de semana del modelo = lunes 00:00 (calendario operativo abstracto).
long quarterOfWeek = Math.round(time() * 672.0) % 672;
int day = (int)(quarterOfWeek / 96);
int quarterOfDay = (int)(quarterOfWeek % 96);
if (day < 5 && quarterOfDay >= 32 && quarterOfDay < 64) {
    // Equivalentes de cajas/h por máquina respecto al cuello de botella.
    // Envasado (índice 3) fija la capacidad nominal ps.weeklyCapacity.
    double[] relativeSpeed = {1.30, 1.15, 1.10, 1.00, 1.20, 1.25};
    for (int i = 0; i < productionLines.size(); i++) {
        ProductionLineState line = productionLines.get(i);
        ProductState ps = inventorySystem.get(i); // mismas posiciones desde startup

        // Llegadas tras un viaje de cuatro intervalos (1 h) por tramo.
        for (int stage = 0; stage < 6; stage++) {
            double arrived = line.transit[stage][0];
            for (int k = 0; k < 3; k++)
                line.transit[stage][k] = line.transit[stage][k + 1];
            line.transit[stage][3] = 0;
            if (stage == 5) {
                ps.inventory += arrived;
                line.finished += arrived;
            } else line.queue[stage + 1] += arrived;
        }

        // Procesar de atrás hacia delante impide pasar por dos máquinas
        // durante el mismo intervalo de tiempo.
        for (int stage = 5; stage >= 0; stage--) {
            if (line.repairTicks[stage] > 0) {
                line.repairTicks[stage]--;
                continue;
            }
            // Fallos: media de 160 h entre averías por máquina;
            // reparación supuesta de 2 h (8 intervalos).
            if (uniform(0, 1) < 0.25 / 160.0) {
                line.repairTicks[stage] = 8;
                line.failures++;
                continue;
            }
            // 40 h/semana y 4 intervalos por hora -> 160 intervalos.
            double service = ps.weeklyCapacity * relativeSpeed[stage] / 160.0;
            double done = Math.min(line.queue[stage], service);
            line.queue[stage] -= done;
            line.transit[stage][3] += done;
            line.processed[stage] += done;
        }
        // Satisfacer atrasos en cuanto entra producto terminado al depósito.
        double recovered = Math.min(ps.inventory, ps.backlog);
        ps.inventory -= recovered;
        ps.backlog -= recovered;
    }
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(0).transit[0][k];
  cajas_lavandina_0.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavandina_0.setX(659 + (677 - 659) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(0).transit[1][k];
  cajas_lavandina_1.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavandina_1.setX(775 + (793 - 775) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(0).transit[2][k];
  cajas_lavandina_2.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavandina_2.setX(891 + (909 - 891) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(0).transit[3][k];
  cajas_lavandina_3.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavandina_3.setX(1007 + (1025 - 1007) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(0).transit[4][k];
  cajas_lavandina_4.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavandina_4.setX(1123 + (1141 - 1123) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(0).transit[5][k];
  cajas_lavandina_5.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavandina_5.setX(1239 + (1300 - 1239) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(1).transit[0][k];
  cajas_desinfectante_0.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_desinfectante_0.setX(659 + (677 - 659) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(1).transit[1][k];
  cajas_desinfectante_1.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_desinfectante_1.setX(775 + (793 - 775) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(1).transit[2][k];
  cajas_desinfectante_2.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_desinfectante_2.setX(891 + (909 - 891) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(1).transit[3][k];
  cajas_desinfectante_3.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_desinfectante_3.setX(1007 + (1025 - 1007) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(1).transit[4][k];
  cajas_desinfectante_4.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_desinfectante_4.setX(1123 + (1141 - 1123) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(1).transit[5][k];
  cajas_desinfectante_5.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_desinfectante_5.setX(1239 + (1300 - 1239) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(2).transit[0][k];
  cajas_lavavajilla_0.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavavajilla_0.setX(659 + (677 - 659) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(2).transit[1][k];
  cajas_lavavajilla_1.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavavajilla_1.setX(775 + (793 - 775) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(2).transit[2][k];
  cajas_lavavajilla_2.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavavajilla_2.setX(891 + (909 - 891) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(2).transit[3][k];
  cajas_lavavajilla_3.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavavajilla_3.setX(1007 + (1025 - 1007) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(2).transit[4][k];
  cajas_lavavajilla_4.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavavajilla_4.setX(1123 + (1141 - 1123) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(2).transit[5][k];
  cajas_lavavajilla_5.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavavajilla_5.setX(1239 + (1300 - 1239) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(3).transit[0][k];
  cajas_lavarropa_0.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavarropa_0.setX(659 + (677 - 659) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(3).transit[1][k];
  cajas_lavarropa_1.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavarropa_1.setX(775 + (793 - 775) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(3).transit[2][k];
  cajas_lavarropa_2.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavarropa_2.setX(891 + (909 - 891) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(3).transit[3][k];
  cajas_lavarropa_3.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavarropa_3.setX(1007 + (1025 - 1007) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(3).transit[4][k];
  cajas_lavarropa_4.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavarropa_4.setX(1123 + (1141 - 1123) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(3).transit[5][k];
  cajas_lavarropa_5.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_lavarropa_5.setX(1239 + (1300 - 1239) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(4).transit[0][k];
  cajas_suavizante_0.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_suavizante_0.setX(659 + (677 - 659) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(4).transit[1][k];
  cajas_suavizante_1.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_suavizante_1.setX(775 + (793 - 775) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(4).transit[2][k];
  cajas_suavizante_2.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_suavizante_2.setX(891 + (909 - 891) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(4).transit[3][k];
  cajas_suavizante_3.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_suavizante_3.setX(1007 + (1025 - 1007) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(4).transit[4][k];
  cajas_suavizante_4.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_suavizante_4.setX(1123 + (1141 - 1123) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(4).transit[5][k];
  cajas_suavizante_5.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_suavizante_5.setX(1239 + (1300 - 1239) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(5).transit[0][k];
  cajas_detergente_0.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_detergente_0.setX(659 + (677 - 659) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(5).transit[1][k];
  cajas_detergente_1.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_detergente_1.setX(775 + (793 - 775) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(5).transit[2][k];
  cajas_detergente_2.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_detergente_2.setX(891 + (909 - 891) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(5).transit[3][k];
  cajas_detergente_3.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_detergente_3.setX(1007 + (1025 - 1007) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(5).transit[4][k];
  cajas_detergente_4.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_detergente_4.setX(1123 + (1141 - 1123) * ((quarterOfWeek % 4) + 1) / 4.0);
}
{ double inMovement = 0;
  for (int k = 0; k < 4; k++) inMovement += productionLines.get(5).transit[5][k];
  cajas_detergente_5.setVisible(inMovement > 0.01);
  if (inMovement > 0.01) cajas_detergente_5.setX(1239 + (1300 - 1239) * ((quarterOfWeek % 4) + 1) / 4.0);
}
double wipLav = (queueMateriaPrima.size() + delayDilucion.size() + delayQCLavandina.size() + queueTanquePulmon.size() + delayEnvasado.size()) * 1000.0;
double wipDes = (tankDesinfectante.size() + delayEnvasadoDesinfectante.size()) * 1000.0;
double wipLvj = (tankLavavajilla.size() + delayEnvasadoLavavajilla.size()) * 1000.0;
double wipLvr = (tankLavarropa.size() + delayEnvasadoLavarropa.size()) * 1000.0;
double wipSua = (tankSuavizante.size() + delayEnvasadoSuavizante.size()) * 1000.0;
double wipDet = (tankDetergente.size() + delayEnvasadoDetergente.size()) * 1000.0;

estado_lavandina.setText("lavandina: WIP " + Math.round(wipLav)
        + " | stock " + Math.round(inventorySystem.get(0).inventory)
        + " | en viaje " + Math.round(inventorySystem.get(0).onOrder)
        + " | atrasos " + Math.round(inventorySystem.get(0).backlog));

estado_desinfectante.setText("desinfectante: WIP " + Math.round(wipDes)
        + " | stock " + Math.round(inventorySystem.get(1).inventory)
        + " | en viaje " + Math.round(inventorySystem.get(1).onOrder)
        + " | atrasos " + Math.round(inventorySystem.get(1).backlog));

estado_lavavajilla.setText("lavavajilla: WIP " + Math.round(wipLvj)
        + " | stock " + Math.round(inventorySystem.get(2).inventory)
        + " | en viaje " + Math.round(inventorySystem.get(2).onOrder)
        + " | atrasos " + Math.round(inventorySystem.get(2).backlog));

estado_lavarropa.setText("lavarropa: WIP " + Math.round(wipLvr)
        + " | stock " + Math.round(inventorySystem.get(3).inventory)
        + " | en viaje " + Math.round(inventorySystem.get(3).onOrder)
        + " | atrasos " + Math.round(inventorySystem.get(3).backlog));

estado_suavizante.setText("suavizante: WIP " + Math.round(wipSua)
        + " | stock " + Math.round(inventorySystem.get(4).inventory)
        + " | en viaje " + Math.round(inventorySystem.get(4).onOrder)
        + " | atrasos " + Math.round(inventorySystem.get(4).backlog));

estado_detergente.setText("detergente: WIP " + Math.round(wipDet)
        + " | stock " + Math.round(inventorySystem.get(5).inventory)
        + " | en viaje " + Math.round(inventorySystem.get(5).onOrder)
        + " | atrasos " + Math.round(inventorySystem.get(5).backlog));
/*ALCODEEND*/}

