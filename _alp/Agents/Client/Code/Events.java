void generateDemand()
{/*ALCODESTART::1787748438766*/
// Código corregido para el Action de generateDemand en Client:
for(ProductType prod : ProductType.values()) {
    double mean = 0.0;
    double std = 0.0;

    if (this.clientName.equals("Maxiconsumo")) {
        if (prod == ProductType.LAVANDINA) { mean = 9379; std = 11162; }
        else if (prod == ProductType.LIQUIDO_DESINFECTANTE) { mean = 6171; std = 8216; }
        else if (prod == ProductType.LAVAVAJILLA) { mean = 5104; std = 6055; }
        else if (prod == ProductType.LIQUIDO_LAVAR_ROPA) { mean = 2184; std = 3587; }
        else if (prod == ProductType.SUAVIZANTE) { mean = 1765; std = 2348; }
        else if (prod == ProductType.DETERGENTE_CONCENTRADO) { mean = 1046; std = 1825; }
    }
    else if (this.clientName.equals("Grandes Clientes")) {
        if (prod == ProductType.LAVANDINA) { mean = 3073; std = 2665; }
        else if (prod == ProductType.LIQUIDO_DESINFECTANTE) { mean = 4568; std = 5515; }
        else if (prod == ProductType.LAVAVAJILLA) { mean = 2081; std = 2215; }
        else if (prod == ProductType.LIQUIDO_LAVAR_ROPA) { mean = 312; std = 482; }
        else if (prod == ProductType.SUAVIZANTE) { mean = 516; std = 809; }
    }
    else if (this.clientName.equals("Red Propia")) {
        if (prod == ProductType.LAVANDINA) { mean = 13829; std = 6751; }
        else if (prod == ProductType.LIQUIDO_DESINFECTANTE) { mean = 6780; std = 3723; }
        else if (prod == ProductType.LAVAVAJILLA) { mean = 5575; std = 2569; }
        else if (prod == ProductType.LIQUIDO_LAVAR_ROPA) { mean = 2931; std = 2206; }
        else if (prod == ProductType.SUAVIZANTE) { mean = 2222; std = 1238; }
        else if (prod == ProductType.DETERGENTE_CONCENTRADO) { mean = 1169; std = 1082; }
    }

    if (mean > 0) {
        double orderQty = Math.round(Math.max(0, normal(std, mean)));
        if (orderQty > 0) {
            ((Main)get_Main()).demandaHistorica += orderQty;
            ((Main)get_Main()).demandaSemanalActual += orderQty; // Suma al total semanal de Main
            
            OrderMessage myOrder = new OrderMessage(prod, orderQty);
            send(myOrder, ((Main)get_Main()).domitecPlant);
        }
    }
}
/*ALCODEEND*/}

