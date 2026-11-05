import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/** Acumula 100 ternas por semilla y publica el paquete estadístico sin depender de AnyLogic. */
public final class EstudioPareado {
    private static final int N = 100;
    private static final int ESCENARIOS = 3;
    private static final String VERSION_MODELO = "Domitec_Main_3D; AnyLogic 8.9.10";
    private static final DateTimeFormatter FORMATO_UTC =
            DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss_SSS").withZone(ZoneOffset.UTC);

    private final ComparacionEscenarios comparacion = new ComparacionEscenarios();
    private final StringBuilder resultadosCsv = new StringBuilder(
            "seed,escenario,firma_demanda,warmup_semanas,fillRate,backlog,stock,bw,produccion\n");
    private final StringBuilder seriesCsv = new StringBuilder(
            "seed,escenario,semana,demanda,ordenes,produccion,stock,backlog,wip\n");
    private final ComparacionEscenarios.Resultado[] terna = new ComparacionEscenarios.Resultado[ESCENARIOS];
    private final String[] firmas = new String[ESCENARIOS];
    private final String[] series = new String[ESCENARIOS];
    private int registros = 0;
    private boolean terminado = false;
    private String salida = "";
    private Double warmupEstudio = null;

    /**
     * Agrega una corrida ya finalizada por el experimento de variación de parámetros.
     * El principal debe validar antes número de semanas y número de entradas de demanda.
     */
    public synchronized void agregar(ComparacionEscenarios.Resultado resultado,
                                     String firmaDemanda,
                                     String serieCsv,
                                     double warmupSemanas,
                                     ConfiguracionDomitec configuracion,
                                     String destino) {
        try {
            validarSiguiente(resultado, firmaDemanda, serieCsv, warmupSemanas, configuracion);
            iniciarSesionSiHaceFalta(configuracion, destino);

            final int seed = resultado.seed;
            final int escenario = resultado.escenario;
            final int seedEsperada = registros / ESCENARIOS + 1;
            final int escenarioEsperado = registros % ESCENARIOS;
            terna[escenario] = resultado;
            firmas[escenario] = firmaDemanda;
            series[escenario] = soloFilas(serieCsv);
            registros++;
            SesionEstudio.progreso = registros;
            SesionEstudio.estado = "Corrida " + registros + "/300 (semilla " + seed + ", escenario " + escenario + ")";

            if (escenario == ESCENARIOS - 1) {
                verificarFirmas(seed);
                for (int s = 0; s < ESCENARIOS; s++) {
                    comparacion.agregar(terna[s]);
                    ComparacionEscenarios.Resultado r = terna[s];
                    resultadosCsv.append(seed).append(',').append(s).append(',').append(firmas[s]).append(',')
                            .append(warmupSemanas).append(',').append(r.fillRate).append(',').append(r.backlog).append(',')
                            .append(r.stock).append(',').append(r.bw).append(',').append(r.produccion).append('\n');
                    seriesCsv.append(series[s]);
                }
                SesionEstudio.ultimoResumen = "Semilla " + seed + ": 3 escenarios, demanda base verificada; "
                        + "fillRate=" + terna[0].fillRate + "," + terna[1].fillRate + "," + terna[2].fillRate;
                limpiarTerna();
            }

            if (registros == N * ESCENARIOS) finalizarExitoso(configuracion, destino);
        } catch (Throwable error) {
            if (SesionEstudio.ejecutando) SesionEstudio.finalizar(mensajeError(error));
            if (error instanceof Error) throw (Error) error;
            if (error instanceof RuntimeException) throw (RuntimeException) error;
            throw new RuntimeException(error);
        }
    }

    public synchronized int getCount() { return comparacion.getCount(); }
    public synchronized boolean isTerminado() { return terminado; }
    public synchronized String getSalida() { return salida; }

    private void validarSiguiente(ComparacionEscenarios.Resultado r, String firma, String seriesCsv,
                                  double warmup, ConfiguracionDomitec cfg) {
        if (terminado || registros >= N * ESCENARIOS) throw new IllegalStateException("El estudio ya terminó");
        if (r == null || cfg == null) throw new IllegalArgumentException("resultado/configuración no pueden ser null");
        if (r.seed != registros / ESCENARIOS + 1)
            throw new IllegalArgumentException("Semilla fuera de orden: se esperaba " + (registros / ESCENARIOS + 1));
        if (r.escenario != registros % ESCENARIOS)
            throw new IllegalArgumentException("Escenario fuera de orden: se esperaba " + (registros % ESCENARIOS));
        if (firma == null || !firma.matches("[0-9a-fA-F]{64}"))
            throw new IllegalArgumentException("firmaDemanda debe ser SHA-256 hexadecimal");
        if (seriesCsv == null || !seriesCsv.startsWith("seed,escenario,semana,"))
            throw new IllegalArgumentException("serieCsv debe proceder de RegistroCorrida.seriesCsv");
        if (!finito(warmup) || warmup < 0.0 || warmup >= 100.0)
            throw new IllegalArgumentException("warmupSemanas debe ser finito y estar en [0,100)");
        if (Math.abs(warmup - cfg.calentamiento) > 1e-9)
            throw new IllegalArgumentException("warmupSemanas debe coincidir con configuracion.calentamiento");
        if (warmupEstudio != null && Math.abs(warmupEstudio.doubleValue() - warmup) > 1e-9)
            throw new IllegalArgumentException("warmupSemanas cambió durante el lote");
        if (warmupEstudio == null) warmupEstudio = warmup;
        if (SesionEstudio.cancelar && registros % ESCENARIOS == 0)
            throw new java.util.concurrent.CancellationException("Cancelado antes de comenzar una nueva terna");
    }

    private void iniciarSesionSiHaceFalta(ConfiguracionDomitec cfg, String destino) {
        if (!SesionEstudio.ejecutando) {
            if (registros != 0 || !SesionEstudio.iniciar())
                throw new IllegalStateException("No se pudo iniciar la sesión de estudio");
            SesionEstudio.configuracionEnCurso = cfg.copiarDeep();
            SesionEstudio.carpetaEnCurso = Paths.get(System.getProperty("user.dir"), "resultados_domitec").toString();
        }
        if (SesionEstudio.configuracionEnCurso == null)
            SesionEstudio.configuracionEnCurso = cfg.copiarDeep();
        if (destino != null && !destino.trim().isEmpty()) SesionEstudio.carpetaEnCurso = destino;
    }

    private void verificarFirmas(int seed) {
        if (firmas[0] == null || !firmas[0].equals(firmas[1]) || !firmas[0].equals(firmas[2]))
            throw new IllegalStateException("Firma de demanda distinta entre escenarios en seed " + seed
                    + ": " + firmas[0] + " / " + firmas[1] + " / " + firmas[2]);
    }

    private String soloFilas(String csv) {
        int nl = csv.indexOf('\n');
        if (nl < 0 || nl == csv.length() - 1) throw new IllegalArgumentException("serieCsv no contiene datos semanales");
        return csv.substring(nl + 1);
    }

    private void limpiarTerna() {
        for (int i = 0; i < ESCENARIOS; i++) { terna[i] = null; firmas[i] = null; series[i] = null; }
    }

    private void finalizarExitoso(ConfiguracionDomitec cfg, String destino) throws IOException {
        if (comparacion.getCount() != 300 || comparacion.getTernasOrdenadas().size() != 100)
            throw new IllegalStateException("Resultados incompletos: " + comparacion.getCount());
        String stamp = FORMATO_UTC.format(Instant.now());
        ConfiguracionDomitec configMetadata = SesionEstudio.configuracionEnCurso == null
                ? cfg : SesionEstudio.configuracionEnCurso;
        String metadata = metadata(stamp, configMetadata);
        String csvIC = construirIC();
        Path carpeta = publicarAtomico(destino, stamp, resultadosCsv.toString(), seriesCsv.toString(), csvIC, metadata);
        salida = carpeta.toString();
        terminado = true;
        SesionEstudio.progreso = 300;
        SesionEstudio.ultimoResumen = "Estudio terminado: 300 corridas, 100 ternas. Salida: " + salida;
        // Se publica una sola vez al cerrar la sesión; después no habrá más mutaciones.
        SesionEstudio.finalizar(null, comparacion);
    }

    private String construirIC() {
        StringBuilder b = new StringBuilder("escenario_a,escenario_b,metrica,n,df,media,desviacion,sem,t_critico,ic95_inferior,ic95_superior\n");
        int[][] pares = {{0,1},{0,2},{1,2}};
        String[] metricas = {"fillRate", "backlog", "stock", "bw", "produccion"};
        for (int[] p : pares) for (String metrica : metricas) {
            ComparacionEscenarios.PairCI95 ci = comparacion.pairCI95(p[0], p[1], metrica);
            if (!ci.disponible || ci.n != 100 || ci.df != 99)
                throw new IllegalStateException("IC pareado incompleto para " + metrica);
            b.append(ci.escenarioA).append(',').append(ci.escenarioB).append(',').append(metrica).append(',')
                    .append(ci.n).append(',').append(ci.df).append(',').append(ci.media).append(',')
                    .append(ci.desviacion).append(',').append(ci.sem).append(',').append(ci.tCritico).append(',')
                    .append(ci.inferior).append(',').append(ci.superior).append('\n');
        }
        return b.toString();
    }

    private String metadata(String stamp, ConfiguracionDomitec cfg) {
        StringBuilder b = new StringBuilder();
        b.append("created_utc=").append(Instant.now().toString()).append('\n')
                .append("run_id=").append(stamp).append('\n')
                .append("model_version=").append(VERSION_MODELO).append('\n')
                .append("seeds=1..100\nscenarios=0,1,2\nreplicas=100\nrun_count=300\nweeks=100\n")
                .append("warmup_weeks=").append(cfg.calentamiento).append('\n')
                .append("warmup_policy=Main.resultadoFinal excludes weeks before configured warmup; finite horizon\n")
                .append("common_demand=equal firmaDemanda SHA-256 within each seed\n")
                .append("paired_ci=two-sided Student t 95%, matched by seed, scenario_a minus scenario_b\n")
                .append("\n[configuracion_domitec]\n");
        b.append("mermaLav=").append(cfg.mermaLav).append('\n').append("mermaLiq=").append(cfg.mermaLiq).append('\n')
                .append("tiemposFactor=").append(cfg.tiemposFactor).append('\n').append("capacidadFactor=").append(cfg.capacidadFactor).append('\n')
                .append("factLatigo=").append(cfg.factLatigo).append('\n').append("horas=").append(cfg.horas).append('\n')
                .append("calentamiento=").append(cfg.calentamiento).append('\n').append("reactores=").append(cfg.reactores).append('\n')
                .append("cola=").append(cfg.cola).append('\n').append("tanque=").append(cfg.tanque).append('\n');
        vector(b, "leadDias", cfg.leadDias); vector(b, "cobertura", cfg.cobertura); vector(b, "rate", cfg.rate);
        for (int i = 0; i < cfg.medias.length; i++) vector(b, "medias[" + i + "]", cfg.medias[i]);
        for (int i = 0; i < cfg.desvios.length; i++) vector(b, "desvios[" + i + "]", cfg.desvios[i]);
        return b.toString();
    }

    private void vector(StringBuilder b, String nombre, double[] valores) {
        b.append(nombre).append('=');
        for (int i = 0; i < valores.length; i++) { if (i > 0) b.append(','); b.append(valores[i]); }
        b.append('\n');
    }

    private Path publicarAtomico(String destino, String stamp, String datos, String series,
                                 String ic, String metadata) throws IOException {
        String baseText = destino == null || destino.trim().isEmpty()
                ? SesionEstudio.carpetaEnCurso : destino;
        Path base = Paths.get(baseText).toAbsolutePath().normalize();
        Files.createDirectories(base);
        Path staging = Files.createTempDirectory(base, ".estudio-" + stamp + "-");
        boolean publicado = false;
        try {
            escribir(staging.resolve("resultados.csv"), datos);
            escribir(staging.resolve("series_semanales.csv"), series);
            escribir(staging.resolve("ic_pareados.csv"), ic);
            escribir(staging.resolve("metadata.txt"), metadata);
            Path finalDir = base.resolve("comparacion_" + stamp);
            if (Files.exists(finalDir)) finalDir = base.resolve("comparacion_" + stamp + "_" + UUID.randomUUID());
            try { Files.move(staging, finalDir, StandardCopyOption.ATOMIC_MOVE); }
            catch (AtomicMoveNotSupportedException e) { Files.move(staging, finalDir); }
            publicado = true;
            return finalDir;
        } finally {
            if (!publicado && Files.exists(staging)) borrarTemporal(staging);
        }
    }

    private void escribir(Path p, String s) throws IOException {
        Files.write(p, s.getBytes(StandardCharsets.UTF_8));
    }

    private void borrarTemporal(Path dir) throws IOException {
        java.util.stream.Stream<Path> paths = Files.walk(dir);
        try { paths.sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
            try { Files.deleteIfExists(p); } catch (IOException e) { throw new RuntimeException(e); }
        }); } finally { paths.close(); }
    }

    private String mensajeError(Throwable e) {
        String m = e.getMessage();
        return e.getClass().getSimpleName() + (m == null || m.trim().isEmpty() ? "" : ": " + m);
    }

    private static boolean finito(double d) { return !Double.isNaN(d) && !Double.isInfinite(d); }
}
