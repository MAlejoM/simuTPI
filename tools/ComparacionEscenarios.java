import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Acumulador puro Java para comparar tres escenarios con numeros aleatorios
 * comunes. No depende de AnyLogic ni consume estado de un generador global.
 */
public final class ComparacionEscenarios implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final int ESCENARIOS = 3;
    public static final int SEMILLA_MIN = 1;
    public static final int SEMILLA_MAX = 100;

    /** Una observacion final (o ya agregada para la ventana elegida) de una corrida. */
    public static final class Resultado implements Serializable {
        private static final long serialVersionUID = 1L;
        public final int seed;
        public final int escenario;
        public final double fillRate;
        public final double backlog;
        public final double stock;
        public final double bw;
        public final double produccion;
        public final double canceladas;
        public final double wipMax;
        public final double insumosFinal;

        public Resultado(int seed, int escenario, double fillRate, double backlog,
                         double stock, double bw, double produccion) {
            this(seed, escenario, fillRate, backlog, stock, bw, produccion, 0.0, 0.0, 0.0);
        }

        public Resultado(int seed, int escenario, double fillRate, double backlog,
                         double stock, double bw, double produccion, double canceladas,
                         double wipMax, double insumosFinal) {
            if (seed < SEMILLA_MIN || seed > SEMILLA_MAX)
                throw new IllegalArgumentException("seed debe estar entre 1 y 100");
            if (escenario < 0 || escenario >= ESCENARIOS)
                throw new IllegalArgumentException("escenario debe ser 0, 1 o 2");
            exigirFinito("fillRate", fillRate);
            exigirFinito("backlog", backlog);
            exigirFinito("stock", stock);
            exigirFinito("bw", bw);
            exigirFinito("produccion", produccion);
            exigirFinito("canceladas", canceladas);
            exigirFinito("wipMax", wipMax);
            exigirFinito("insumosFinal", insumosFinal);
            this.seed = seed;
            this.escenario = escenario;
            this.fillRate = fillRate;
            this.backlog = backlog;
            this.stock = stock;
            this.bw = bw;
            this.produccion = produccion;
            this.canceladas = canceladas;
            this.wipMax = wipMax;
            this.insumosFinal = insumosFinal;
        }

        private static void exigirFinito(String nombre, double valor) {
            if (Double.isNaN(valor) || Double.isInfinite(valor))
                throw new IllegalArgumentException(nombre + " debe ser finito");
        }
    }

    /** IC t bilateral 95% de la diferencia pareada (primer escenario menos segundo). */
    public static final class PairCI95 implements Serializable {
        private static final long serialVersionUID = 1L;
        public final int escenarioA, escenarioB, n, df;
        public final double media, desviacion, sem, tCritico, inferior, superior;
        public final boolean disponible;

        private PairCI95(int a, int b, int n, double media, double desviacion,
                         double tCritico, double inferior, double superior) {
            this.escenarioA = a; this.escenarioB = b; this.n = n; this.df = n - 1;
            this.media = media; this.desviacion = desviacion;
            this.sem = n > 0 ? desviacion / Math.sqrt(n) : Double.NaN;
            this.tCritico = tCritico; this.inferior = inferior; this.superior = superior;
            this.disponible = n >= 2;
        }
    }

    private final Map<Long, Resultado> resultados = new LinkedHashMap<Long, Resultado>();

    public void agregar(Resultado resultado) {
        if (resultado == null) throw new IllegalArgumentException("resultado no puede ser null");
        long key = clave(resultado.seed, resultado.escenario);
        if (resultados.containsKey(key))
            throw new IllegalArgumentException("Ya existe resultado para seed=" + resultado.seed
                    + ", escenario=" + resultado.escenario);
        resultados.put(key, resultado);
    }

    public int getCount() { return resultados.size(); }
    public int cantidadResultados() { return getCount(); }

    /** Lista plana ordenada por seed y luego escenario, sin exponer el almacenamiento. */
    public List<Resultado> ternasOrdenadas() {
        List<Resultado> lista = new ArrayList<Resultado>(resultados.values());
        Collections.sort(lista, new Comparator<Resultado>() {
            public int compare(Resultado a, Resultado b) {
                int c = Integer.compare(a.seed, b.seed);
                return c != 0 ? c : Integer.compare(a.escenario, b.escenario);
            }
        });
        return Collections.unmodifiableList(lista);
    }

    /** Solo devuelve ternas completas; cada tripleta está ordenada por escenario. */
    public List<List<Resultado>> getTernasOrdenadas() {
        Map<Integer, Resultado[]> porSeed = new LinkedHashMap<Integer, Resultado[]>();
        for (Resultado r : resultados.values()) {
            Resultado[] terna = porSeed.get(r.seed);
            if (terna == null) { terna = new Resultado[ESCENARIOS]; porSeed.put(r.seed, terna); }
            terna[r.escenario] = r;
        }
        List<Integer> semillas = new ArrayList<Integer>(porSeed.keySet());
        Collections.sort(semillas);
        List<List<Resultado>> salida = new ArrayList<List<Resultado>>();
        for (Integer seed : semillas) {
            Resultado[] t = porSeed.get(seed);
            if (t[0] != null && t[1] != null && t[2] != null) {
                List<Resultado> tripleta = new ArrayList<Resultado>(ESCENARIOS);
                Collections.addAll(tripleta, t);
                salida.add(Collections.unmodifiableList(tripleta));
            }
        }
        return Collections.unmodifiableList(salida);
    }

    /** ICs para las tres parejas y las cinco metricas disponibles. */
    public Map<String, PairCI95> pairCI95() {
        Map<String, PairCI95> salida = new LinkedHashMap<String, PairCI95>();
        int[][] parejas = {{0,1},{0,2},{1,2}};
        String[] metricas = {"fillRate", "backlog", "stock", "bw", "produccion"};
        for (int[] p : parejas) for (String metrica : metricas)
            salida.put("escenario" + p[0] + "-" + p[1] + "." + metrica,
                    pairCI95(p[0], p[1], metrica));
        return Collections.unmodifiableMap(salida);
    }

    public PairCI95 pairCI95(int escenarioA, int escenarioB, String metrica) {
        validarPareja(escenarioA, escenarioB);
        final int a = escenarioA, b = escenarioB;
        List<Double> diferencias = new ArrayList<Double>();
        for (int seed = SEMILLA_MIN; seed <= SEMILLA_MAX; seed++) {
            Resultado ra = resultados.get(clave(seed, a));
            Resultado rb = resultados.get(clave(seed, b));
            if (ra != null && rb != null)
                diferencias.add(valor(ra, metrica) - valor(rb, metrica));
        }
        int n = diferencias.size();
        if (n == 0) return new PairCI95(a,b,0,Double.NaN,Double.NaN,Double.NaN,Double.NaN,Double.NaN);
        double media = 0.0;
        for (double d : diferencias) media += d;
        media /= n;
        double suma = 0.0;
        for (double d : diferencias) { double e = d - media; suma += e * e; }
        double sd = n > 1 ? Math.sqrt(suma / (n - 1)) : Double.NaN;
        if (n < 2) return new PairCI95(a,b,n,media,sd,Double.NaN,Double.NaN,Double.NaN);
        double t = tCritico95(n - 1);
        double margen = t * sd / Math.sqrt(n);
        // Asegura CI exactamente de ancho cero para diferencias constantes.
        if (sd == 0.0) margen = 0.0;
        return new PairCI95(a,b,n,media,sd,t,media-margen,media+margen);
    }

    /** Error t bilateral 95% por df; tabla exacta en df=1..30 y puntos usuales. */
    public static double tCritico95(int df) {
        if (df < 1) throw new IllegalArgumentException("df debe ser >= 1");
        double[] t = {0,12.7062047364,4.30265272975,3.18244630528,2.77644510520,
            2.57058183564,2.44691184879,2.36462425101,2.30600413503,2.26215716285,
            2.22813885196,2.20098516008,2.17881282966,2.16036865646,2.14478668792,
            2.13144954556,2.11990529922,2.10981557783,2.10092204024,2.09302405441,
            2.08596344727,2.07961384473,2.07387306790,2.06865761042,2.06389856163,
            2.05953855275,2.05552943864,2.05183051648,2.04840714180,2.04522964213,
            2.04227245630};
        if (df <= 30) return t[df];
        if (df == 40) return 2.02107539031;
        if (df == 60) return 2.00029782201;
        if (df == 99) return 1.9842169515;
        if (df >= 120) return 1.95996398454;
        // Interpolacion lineal de cuantiles tabulados de Student.
        int[] dfs = {30,40,60,99,120};
        double[] ts = {2.04227245630,2.02107539031,2.00029782201,1.9842169515,1.97993040505};
        for (int i=0; i<dfs.length-1; i++) if (df < dfs[i+1]) {
            double f = (df-dfs[i])/(double)(dfs[i+1]-dfs[i]);
            return ts[i] + f*(ts[i+1]-ts[i]);
        }
        return 1.95996398454;
    }

    /** Uniforme determinista U[0,1), separado por seed/canal/producto/indice/etapa. */
    public static double uniforme(long semilla, int canal, int producto, long indice, int etapa) {
        long h = mezclar(semilla ^ 0x9E3779B97F4A7C15L);
        h = mezclar(h ^ (((long) canal) * 0xD1B54A32D192ED03L));
        h = mezclar(h ^ (((long) producto) * 0x94D049BB133111EBL));
        h = mezclar(h ^ (indice * 0xBF58476D1CE4E5B9L));
        h = mezclar(h ^ (((long) etapa) * 0xDB4F0B9175AE2165L));
        return (h >>> 11) * 0x1.0p-53;
    }

    /** Normal determinista por Box-Muller con canal de salt distinto del uniforme publico. */
    public static double normal(long seed, int canal, int producto, long semana,
                                double media, double desvio) {
        if (Double.isNaN(media) || Double.isInfinite(media) || Double.isNaN(desvio)
                || Double.isInfinite(desvio) || desvio < 0.0)
            throw new IllegalArgumentException("media finita y desvio finito no negativo requeridos");
        double u1 = uniforme(seed ^ 0xA0761D6478BD642FL, canal, producto, semana, 0x4E31);
        double u2 = uniforme(seed ^ 0xE7037ED1A0B428DBL, canal, producto, semana, 0x4E32);
        if (u1 == 0.0) u1 = 0x1.0p-53;
        return media + desvio * Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    }

    public static double triangular(long seed, int producto, long lote, int etapa,
                                    double minimo, double moda, double maximo) {
        if (!finito(minimo) || !finito(moda) || !finito(maximo)
                || minimo > moda || moda > maximo || minimo == maximo)
            throw new IllegalArgumentException("Se requiere minimo <= moda <= maximo y rango positivo");
        double u = uniforme(seed, 0x545249, producto, lote, etapa);
        double corte = (moda - minimo) / (maximo - minimo);
        if (u < corte) return minimo + Math.sqrt(u * (maximo-minimo) * (moda-minimo));
        return maximo - Math.sqrt((1.0-u) * (maximo-minimo) * (maximo-moda));
    }

    /** CSV serializable en memoria (sin escritura a disco). */
    public static String toCsv(ComparacionEscenarios datos) {
        StringBuilder b = new StringBuilder("seed,escenario,fillRate,backlog,stock,bw,produccion\n");
        for (Resultado r : datos.ternasOrdenadas())
            b.append(r.seed).append(',').append(r.escenario).append(',').append(r.fillRate).append(',')
             .append(r.backlog).append(',').append(r.stock).append(',').append(r.bw).append(',')
             .append(r.produccion).append('\n');
        return b.toString();
    }

    public String resumen() {
        StringBuilder b = new StringBuilder("Resultados: ").append(getCount()).append("; ternas completas: ")
                .append(getTernasOrdenadas().size()).append('\n');
        for (Map.Entry<String, PairCI95> e : pairCI95().entrySet()) {
            PairCI95 ci = e.getValue();
            b.append(e.getKey()).append(" n=").append(ci.n);
            if (ci.disponible) b.append(" media=").append(ci.media).append(" IC95%=[")
                    .append(ci.inferior).append(", ").append(ci.superior).append(']');
            else b.append(" (minimo n=2)");
            b.append('\n');
        }
        return b.toString();
    }

    private static boolean finito(double d) { return !Double.isNaN(d) && !Double.isInfinite(d); }
    private static long clave(int seed, int escenario) { return (((long)seed) << 32) | (escenario & 0xffffffffL); }
    private static void validarPareja(int a, int b) {
        if (a < 0 || a >= ESCENARIOS || b < 0 || b >= ESCENARIOS || a == b)
            throw new IllegalArgumentException("La pareja requiere dos escenarios distintos entre 0 y 2");
    }
    private static double valor(Resultado r, String metrica) {
        if ("fillRate".equals(metrica)) return r.fillRate;
        if ("backlog".equals(metrica)) return r.backlog;
        if ("stock".equals(metrica)) return r.stock;
        if ("bw".equals(metrica)) return r.bw;
        if ("produccion".equals(metrica)) return r.produccion;
        throw new IllegalArgumentException("Metrica desconocida: " + metrica);
    }
    private static long mezclar(long z) {
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }
}
