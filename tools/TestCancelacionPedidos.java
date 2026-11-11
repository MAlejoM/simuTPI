/** Pruebas de vencimiento FIFO y metricas de pedidos, sin motor ni mocks. */
public final class TestCancelacionPedidos {
    private static int checks;

    public static void main(String[] args) {
        plazoCeroYCorteExacto();
        parcialFifoYNoEntregaPosterior();
        metricasWarmupYConservacion();
        System.out.println("OK: " + checks + " comprobaciones de cancelacion de pedidos");
    }

    private static void plazoCeroYCorteExacto() {
        RegistroCorrida r = new RegistroCorrida();
        r.pedido(0, 1.0, 5.0, false);
        r.pedido(0, 2.0, 7.0, false);
        eq(0.0, r.cancelarVencidos(0, 0.999, 0.0), "plazo cero aun no vence antes del tiempo");
        eq(5.0, r.cancelarVencidos(0, 1.0, 0.0), "plazo cero vence en tiempo de cohorte");
        eq(0.0, r.cancelarVencidos(0, 3.999, 2.0), "no vence antes del corte");
        eq(7.0, r.cancelarVencidos(0, 4.0, 2.0), "incluye el corte exacto");
        eq(0.0, r.pendienteProducto(0), "cola queda vacia");
    }

    private static void parcialFifoYNoEntregaPosterior() {
        RegistroCorrida r = new RegistroCorrida();
        r.pedido(1, 1.0, 10.0, false);
        r.pedido(1, 2.0, 8.0, false);
        r.diferido(1, 2.5, 4.0);
        eq(14.0, r.cancelarVencidos(1, 3.0, 1.0), "cancela remanente primero y cohorte siguiente");
        eq(0.0, r.pendienteProducto(1), "canceladas salen de la cola FIFO");
        double fillAntes = r.fillRate(0.0);
        r.diferido(1, 4.0, 100.0);
        eq(fillAntes, r.fillRate(0.0), "entrega posterior no se asigna a canceladas");
        eq(14.0, r.canceladoTotal(0.0), "cancelacion parcial contabiliza solo pendiente");

        RegistroCorrida temprano = new RegistroCorrida();
        temprano.pedido(2, 5.0, 2.0, false);
        boolean rechazada = false;
        try { temprano.diferido(2, 4.0, 1.0); }
        catch (IllegalArgumentException ex) { rechazada = true; }
        ok(rechazada, "rechaza atencion anterior a cohorte");
    }

    private static void metricasWarmupYConservacion() {
        RegistroCorrida r = new RegistroCorrida();
        r.pedido(3, 0.0, 10.0, false);
        r.diferido(3, 1.0, 3.0);
        r.pedido(3, 2.0, 20.0, false);
        r.pedido(3, 4.0, 6.0, true);
        r.cancelarVencidos(3, 3.0, 3.0);
        eq(26.0, r.demandaTotal(2.0), "demanda en ventana post warmup");
        eq(0.0, r.canceladoTotal(2.0), "cancelaciones cohorte posterior al warmup cero");
        eq(20.0, r.pendienteTotal(2.0), "pendiente respeta warmup y cumplido");
        eq(6.0 / 26.0, r.fillRate(2.0), "fill rate conserva demanda cancelada en denominador");
        eq(7.0, r.canceladoTotal(0.0), "cancelacion total en toda la corrida");
        eq(36.0, r.demandaTotal(0.0), "demanda total");
        eq(20.0, r.pendienteTotal(0.0), "pendiente total");
        eq(36.0, r.demandaTotal(0.0) * r.fillRate(0.0)
                + r.pendienteTotal(0.0) + r.canceladoTotal(0.0),
                "demanda = cumplido + pendiente + cancelado");
    }

    private static void eq(double expected, double actual, String message) {
        if (Math.abs(expected - actual) > 1e-10) throw new AssertionError(message + ": " + expected + " != " + actual);
        checks++;
    }
    private static void ok(boolean value, String message) {
        if (!value) throw new AssertionError(message);
        checks++;
    }
}
