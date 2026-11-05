import java.io.Serializable;
import java.util.Locale;

/** Parametros editables y validables del modelo Domitec, independiente de AnyLogic. */
public final class ConfiguracionDomitec implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final String[] PRODUCTOS = {
        "LAVANDINA", "LIQUIDO_DESINFECTANTE", "LAVAVAJILLA",
        "LIQUIDO_LAVAR_ROPA", "SUAVIZANTE", "DETERGENTE_CONCENTRADO"
    };

    public double[][] medias = {
        {9379,6171,5104,2184,1765,1046},
        {3073,4568,2081,312,516,0},
        {13829,6780,5575,2931,2222,1169}
    };
    public double[][] desvios = {
        {11162,8216,6055,3587,2348,1825},
        {2665,5515,2215,482,809,0},
        {6751,3723,2569,2206,1238,1082}
    };
    public double[] leadDias = {30,21,21,21,45,21};
    public double[] cobertura = {5.5,4.5,4,4,7.5,4};
    public double[] rate = {667,405,237,176,104,64};
    public double mermaLav = 0.03;
    public double mermaLiq = 0.05;
    public double tiemposFactor = 1.0;
    public double capacidadFactor = 1.0;
    public double factLatigo = 1.5;
    public double horas = 40.0;
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
        c.factLatigo = factLatigo; c.horas = horas; c.calentamiento = calentamiento;
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
        positivo("factLatigo", factLatigo); positivo("horas", horas);
        if (horas > 168.0) throw new IllegalArgumentException("horas no puede superar 168 por semana");
        noNegativo("calentamiento", calentamiento);
        if (calentamiento >= 100.0) throw new IllegalArgumentException("calentamiento debe ser < 100 semanas");
        if (reactores < 1 || cola < 1 || tanque < 1)
            throw new IllegalArgumentException("reactores, cola y tanque deben ser >= 1");
        return this;
    }

    /** Variante de capacidad/turno utilizada por cada escenario. */
    public ConfiguracionDomitec escenario(int escenario) {
        if (escenario < 0 || escenario > 2)
            throw new IllegalArgumentException("escenario debe ser 0, 1 o 2");
        ConfiguracionDomitec c = copiarDeep();
        if (escenario == 0) { c.factLatigo = 1.5; c.horas = 40.0; }
        else if (escenario == 1) { c.factLatigo = 1.0; c.horas = 40.0; }
        else { c.factLatigo = 1.0; c.horas = 51.0; }
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
