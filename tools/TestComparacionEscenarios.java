/** Pruebas ejecutables sin framework ni dependencias externas. */
public final class TestComparacionEscenarios {
    private static int comprobaciones;

    public static void main(String[] args) {
        pruebaGeneradoresDeterministas();
        pruebaAgregacionYOrden();
        pruebaICPareado();
        System.out.println("OK: " + comprobaciones + " comprobaciones");
    }

    private static void pruebaGeneradoresDeterministas() {
        double u = ComparacionEscenarios.uniforme(42L, 1, 2, 3L, 4);
        igual(u, ComparacionEscenarios.uniforme(42L, 1, 2, 3L, 4), "uniforme reproducible");
        requiere(u >= 0.0 && u < 1.0, "uniforme dentro de [0,1)");
        requiere(u != ComparacionEscenarios.uniforme(42L, 2, 2, 3L, 4), "canales separados");
        double n = ComparacionEscenarios.normal(42L, 1, 2, 3L, 5.0, 2.0);
        igual(n, ComparacionEscenarios.normal(42L, 1, 2, 3L, 5.0, 2.0), "normal reproducible");
        requiere(!Double.isNaN(n) && !Double.isInfinite(n), "normal finita");
        double tri = ComparacionEscenarios.triangular(42L, 2, 3L, 4, 1.0, 2.0, 5.0);
        igual(tri, ComparacionEscenarios.triangular(42L, 2, 3L, 4, 1.0, 2.0, 5.0), "triangular reproducible");
        requiere(tri >= 1.0 && tri <= 5.0, "triangular dentro del rango");

        // Una tabla semanal de demanda keyed por semana es independiente del orden de consulta.
        double[] tabla = new double[32];
        for (int semana = 0; semana < tabla.length; semana++)
            tabla[semana] = ComparacionEscenarios.normal(91L, 7, 1, semana, 100.0, 10.0);
        for (int semana = tabla.length - 1; semana >= 0; semana--)
            igual(tabla[semana], ComparacionEscenarios.normal(91L, 7, 1, semana, 100.0, 10.0),
                    "demanda semanal independiente del orden");
    }

    private static void pruebaAgregacionYOrden() {
        ComparacionEscenarios c = new ComparacionEscenarios();
        c.agregar(r(2,2,0)); c.agregar(r(1,1,0)); c.agregar(r(1,0,0)); c.agregar(r(1,2,0));
        requiere(c.getCount() == 4, "contador");
        requiere(c.ternasOrdenadas().get(0).seed == 1 && c.ternasOrdenadas().get(0).escenario == 0,
                "orden por seed/escenario");
        requiere(c.getTernasOrdenadas().size() == 1, "solo terna completa");
        esperaIllegal(new Runnable() { public void run() { c.agregar(r(1,2,1)); } }, "duplicado seed/escenario");
        esperaIllegal(new Runnable() { public void run() { new ComparacionEscenarios.Resultado(1,0,Double.NaN,0,0,0,0); } }, "rechaza NaN");
        esperaIllegal(new Runnable() { public void run() { new ComparacionEscenarios.Resultado(101,0,0,0,0,0,0); } }, "rechaza seed fuera del lote 1..100");
    }

    private static void pruebaICPareado() {
        ComparacionEscenarios c = new ComparacionEscenarios();
        for (int seed = 1; seed <= 100; seed++) {
            c.agregar(new ComparacionEscenarios.Resultado(seed,0,10.0+seed,seed,2,3,4));
            c.agregar(new ComparacionEscenarios.Resultado(seed,1,7.0+seed,seed+2,2,3,4));
            c.agregar(new ComparacionEscenarios.Resultado(seed,2,10.0+seed,seed,2,3,4));
        }
        ComparacionEscenarios.PairCI95 ci = c.pairCI95(0,1,"fillRate");
        requiere(ci.n == 100 && ci.df == 99, "n y df pareados");
        igual(3.0, ci.media, "diferencia pareada");
        igual(0.0, ci.inferior - ci.media, "diferencia constante: limite inferior sin ancho");
        igual(0.0, ci.superior - ci.media, "diferencia constante: limite superior sin ancho");
        igual(1.9842169515, ci.tCritico, "t critico exacto df=99");
        requiere(c.pairCI95().size() == 15, "tres parejas por cinco metricas");
        requiere(ComparacionEscenarios.tCritico95(1) > 12.7, "tabla t para n=2");
    }

    private static ComparacionEscenarios.Resultado r(int seed, int escenario, double v) {
        return new ComparacionEscenarios.Resultado(seed, escenario, v, v, v, v, v);
    }
    private static void igual(double esperado, double real, String mensaje) {
        requiere(Double.doubleToLongBits(esperado) == Double.doubleToLongBits(real), mensaje);
    }
    private static void requiere(boolean ok, String mensaje) {
        if (!ok) throw new AssertionError(mensaje);
        comprobaciones++;
    }
    private static void esperaIllegal(Runnable accion, String mensaje) {
        try { accion.run(); } catch (IllegalArgumentException esperado) { comprobaciones++; return; }
        throw new AssertionError(mensaje);
    }
}
