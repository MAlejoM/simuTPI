public final class TestDatosOperativos {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void close(double a, double b, double tolerance, String message) {
        if (Math.abs(a - b) > tolerance) throw new AssertionError(message + ": " + a + " != " + b);
    }

    public static void main(String[] args) {
        int[] days = {31,28,31,30,31,30,31,31,30,31,30,31};
        double[][] means = DatosOperativos.medias();
        double[][] sds = DatosOperativos.desvios();
        check(means.length == 3 && sds.length == 3, "matrices con tres canales");
        for (int c = 0; c < 3; c++) {
            check(means[c].length == 6 && sds[c].length == 6, "matrices con seis productos");
            for (int p = 0; p < 6; p++) {
                double weightedMean = 0.0;
                for (int m = 0; m < 12; m++) {
                    double monthRate = DatosOperativos.tasaMensual(c, p, m);
                    check(!Double.isNaN(monthRate) && !Double.isInfinite(monthRate), "mes presente/finitud");
                    weightedMean += monthRate * days[m] / 365.0;
                }
                close(means[c][p], weightedMean, 1e-9, "media anual ponderada exacta");
                double weightedVariance = 0.0;
                for (int m = 0; m < 12; m++) {
                    double delta = DatosOperativos.tasaMensual(c, p, m) - weightedMean;
                    weightedVariance += days[m] / 365.0 * delta * delta;
                }
                close(sds[c][p], Math.sqrt(weightedVariance), 1e-9, "desvio poblacional ponderado exacto");
            }
        }

        // Cada bloque de cuatro semanas comparte exactamente el mismo mes entre canales/productos.
        for (long block = 0; block < 20; block++) {
            long firstWeek = block * 4;
            int month = DatosOperativos.mesSeleccionado(37L, firstWeek);
            for (int offset = 0; offset < 4; offset++)
                check(month == DatosOperativos.mesSeleccionado(37L, firstWeek + offset), "mismo mes en bloque de cuatro semanas");
            check(month == DatosOperativos.mesSeleccionado(37L, firstWeek), "mes común independiente de canal/producto");
        }

        // Reproducibilidad y bootstrap de la tasa histórica sin recorte.
        for (int c = 0; c < 3; c++) for (int p = 0; p < 6; p++) for (long week = 0; week < 40; week++) {
            double d1 = DatosOperativos.demanda(37L, c, p, week, means[c][p], sds[c][p]);
            double d2 = DatosOperativos.demanda(37L, c, p, week, means[c][p], sds[c][p]);
            close(d1, d2, 0.0, "demanda reproducible");
            check(d1 >= 0.0, "bootstrap histórico no negativo");
        }
        for (int c = 0; c < 3; c++) for (int p = 0; p < 6; p++) {
            long seed = 51L;
            long week = 16L;
            int month = DatosOperativos.mesSeleccionado(seed, week);
            double base = DatosOperativos.tasaMensual(c, p, month);
            double mean = means[c][p], sd = sds[c][p];
            double customMean = mean + 3.0, customSd = sd * 0.5;
            double expected = sd == 0.0 ? customMean : Math.max(0.0, (base - mean) * customSd / sd + customMean);
            close(DatosOperativos.demanda(seed, c, p, week, customMean, customSd), expected, 1e-9, "transformación custom");
        }

        double[][] meanCopy = DatosOperativos.medias();
        meanCopy[0][0] = -12345.0;
        check(DatosOperativos.medias()[0][0] >= 0.0, "medias devuelve copia profunda");
        double[][] sdCopy = DatosOperativos.desvios();
        sdCopy[0][0] = -12345.0;
        check(DatosOperativos.desvios()[0][0] >= 0.0, "desvios devuelve copia profunda");
        double[] rateCopy = DatosOperativos.rates();
        double[] activeCopy = DatosOperativos.ratesActivos();
        double[] fractionCopy = DatosOperativos.fraccionesOperacion();
        check(rateCopy.length == 6 && activeCopy.length == 6 && fractionCopy.length == 6, "seis tasas por producto");
        for (int p = 0; p < 6; p++) {
            check(rateCopy[p] > 0.0 && !Double.isNaN(rateCopy[p]), "rate efectivo positivo");
            check(activeCopy[p] > 0.0 && !Double.isNaN(activeCopy[p]), "rate activo positivo");
            check(fractionCopy[p] > 0.0 && !Double.isNaN(fractionCopy[p]), "fracción de operación positiva");
            close(rateCopy[p] / activeCopy[p], fractionCopy[p], 1e-9, "rate efectivo = rate activo x fracción");
        }
        close(rateCopy[1], 426507.0 / (8.0 * 365.0 / 12.0 * 24.0), 1e-9,
                "índice 1 es desinfectante en orden ConfiguracionDomitec.PRODUCTOS");
        close(rateCopy[2], 470742.0 / (8.0 * 365.0 / 12.0 * 24.0), 1e-9,
                "índice 2 es lavavajilla en orden ConfiguracionDomitec.PRODUCTOS");
        rateCopy[0] = -1.0;
        activeCopy[0] = -1.0;
        fractionCopy[0] = -1.0;
        check(DatosOperativos.rates()[0] > 0.0 && DatosOperativos.ratesActivos()[0] > 0.0
                && DatosOperativos.fraccionesOperacion()[0] > 0.0, "tasas devuelven copias");

        boolean badChannel = false;
        try { DatosOperativos.demanda(1L, 3, 0, 0L, 0.0, 0.0); }
        catch (IllegalArgumentException expected) { badChannel = true; }
        check(badChannel, "valida canal");
        System.out.println("TestDatosOperativos: OK");
    }
}
