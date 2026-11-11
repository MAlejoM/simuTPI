import java.io.Serializable;
import java.util.Locale;

/** Parametros editables y validables del modelo Domitec, independiente de AnyLogic. */
public final class ConfiguracionDomitec implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final String[] PRODUCTOS = {
        "LAVANDINA", "LIQUIDO_DESINFECTANTE", "LAVAVAJILLA",
        "LIQUIDO_LAVAR_ROPA", "SUAVIZANTE", "DETERGENTE_CONCENTRADO"
    };

    public static final String VERSION_MODELO = "operacion-24x7-v2";
    public double[][] medias = DatosOperativos.medias();
    public double[][] desvios = DatosOperativos.desvios();
    public double[] leadDias = {30,21,21,21,45,21};
    public double[] cobertura = {5.5,4.5,4,4,7.5,4};
    // Observed good boxes per opening hour (24x7), including historical allocation.
    public double[] rate = DatosOperativos.rates();
    // Additional experimental scrap only. Observed effective output already includes losses.
    public double mermaLav = 0.0;
    public double mermaLiq = 0.0;
    public double tiemposFactor = 1.0;
    public double capacidadFactor = 1.0;
    public double mejoraEscenario = 1.0;
    public double factLatigo = 1.5;
    public double horas = 168.0;
    /** Scenario assumption, NOT estimated from monthly cancellation totals. */
    public double esperaPedidoDias = 30.0;
    /** Provisional release cards, 6 per line at the default tank setting. */
    public int maxLotesEnProceso = 36;
    public double calentamiento = 15.0;
    public int reactores = 4;
    public int cola = 20;
    public int tanque = 3;

    public static int indice(String productname) {
        if (productname == null) throw new IllegalArgumentException("producto null");
        String nombre = productname.trim().toUpperCase(Locale.ROOT)
                .replace(' ', '_').replace('-', '_');
        for (int i = 0; i < PRODUCTOS.length; i++) if (PRODUCTOS[i].equals(nombre)) return i;
        throw new IllegalArgumentException("Producto desconocido: " + productname);
    }

    public ConfiguracionDomitec copiarDeep() {
        ConfiguracionDomitec c = new ConfiguracionDomitec();
        c.medias = copiar(medias);
        c.desvios = copiar(desvios);
        c.leadDias = copiar(leadDias);
        c.cobertura = copiar(cobertura);
        c.rate = copiar(rate);
        c.mermaLav = mermaLav; c.mermaLiq = mermaLiq;
        c.tiemposFactor = tiemposFactor; c.capacidadFactor = capacidadFactor;
        c.mejoraEscenario = mejoraEscenario;
        c.factLatigo = factLatigo; c.horas = horas; c.calentamiento = calentamiento;
        c.esperaPedidoDias = esperaPedidoDias; c.maxLotesEnProceso = maxLotesEnProceso;
        c.reactores = reactores; c.cola = cola; c.tanque = tanque;
        return c;
    }

    /** Devuelve this para permitir encadenar validacion antes de pasar la configuracion. */
    public ConfiguracionDomitec validar() {
        matriz("medias", medias, true);
        matriz("desvios", desvios, true);
        vector("leadDias", leadDias, true);
        vector("cobertura", cobertura, true);
        vector("rate", rate, true);
        for (int i = 0; i < rate.length; i++)
            if (rate[i] <= 0.0) throw new IllegalArgumentException("rate[" + i + "] debe ser > 0");
        finito("mermaLav", mermaLav); finito("mermaLiq", mermaLiq);
        if (mermaLav < 0.0 || mermaLav > 1.0 || mermaLiq < 0.0 || mermaLiq > 1.0)
            throw new IllegalArgumentException("mermas deben estar entre 0 y 1");
        positivo("tiemposFactor", tiemposFactor); positivo("capacidadFactor", capacidadFactor);
        positivo("mejoraEscenario", mejoraEscenario);
        positivo("factLatigo", factLatigo); positivo("horas", horas);
        if (horas > 168.0) throw new IllegalArgumentException("Calendario 24x7: maximo 168 horas por semana");
        noNegativo("esperaPedidoDias", esperaPedidoDias);
        if (maxLotesEnProceso < 1) throw new IllegalArgumentException("maxLotesEnProceso debe ser >= 1");
        noNegativo("calentamiento", calentamiento);
        if (calentamiento >= 100.0) throw new IllegalArgumentException("calentamiento debe ser < 100 semanas");
        if (reactores < 1 || cola < 1 || tanque < 1)
            throw new IllegalArgumentException("reactores, cola y tanque deben ser >= 1");
        return this;
    }

    /** Scenario policy and throughput hypothesis; the real opening calendar is preserved. */
    public ConfiguracionDomitec escenario(int escenario) {
        if (escenario < 0 || escenario > 2)
            throw new IllegalArgumentException("escenario debe ser 0, 1 o 2");
        ConfiguracionDomitec c = copiarDeep();
        c.mejoraEscenario = 1.0;
        if (escenario == 0) c.factLatigo = 1.5;
        else if (escenario == 1) c.factLatigo = 1.0;
        else {
            c.factLatigo = 1.0;
            // Keep the former 51/40 experimental improvement as a throughput
            // hypothesis; never invent additional hours in a 168-hour week.
            c.mejoraEscenario = 51.0 / 40.0;
        }
        return c;
    }

    /** Factor que convierte una jornada semanal a capacidad de 168 horas. */
    public double escalaTurno() { return 168.0 / horas; }

    private static double[][] copiar(double[][] x) {
        if (x == null) return null;
        double[][] r = new double[x.length][];
        for (int i=0; i<x.length; i++) r[i] = copiar(x[i]);
        return r;
    }
    private static double[] copiar(double[] x) {
        if (x == null) return null;
        double[] r = new double[x.length]; System.arraycopy(x,0,r,0,x.length); return r;
    }
    private static void matriz(String nombre, double[][] m, boolean noNeg) {
        if (m == null || m.length != 3) throw new IllegalArgumentException(nombre + " debe tener 3 filas");
        for (int i=0;i<m.length;i++) vector(nombre + "["+i+"]",m[i],noNeg);
    }
    private static void vector(String nombre, double[] v, boolean noNeg) {
        if (v == null || v.length != 6) throw new IllegalArgumentException(nombre + " debe tener 6 valores");
        for (int i=0;i<v.length;i++) {
            finito(nombre+"["+i+"]",v[i]);
            if (noNeg && v[i] < 0) throw new IllegalArgumentException(nombre+" no admite negativos");
        }
    }
    private static void finito(String n,double v) {
        if (Double.isNaN(v)||Double.isInfinite(v)) throw new IllegalArgumentException(n+" debe ser finito");
    }
    private static void positivo(String n,double v) {
        finito(n,v); if (v <= 0) throw new IllegalArgumentException(n+" debe ser > 0");
    }
    private static void noNegativo(String n,double v) {
        finito(n,v); if (v < 0) throw new IllegalArgumentException(n+" debe ser >= 0");
    }
}
