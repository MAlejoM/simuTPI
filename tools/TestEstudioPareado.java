import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Stream;

/** Prueba de integración de helpers con datos sintéticos efímeros; no son datos del TP. */
public final class TestEstudioPareado {
    private static int checks;

    public static void main(String[] args) throws Exception {
        Path temp = Files.createTempDirectory("fixture-sintetica-estudio-pareado-");
        try {
            probarPublicacionCompleta(temp);
            probarReintentoExportacion(temp);
            probarRechazos(temp);
            System.out.println("OK: " + checks + " comprobaciones de EstudioPareado; fixture sintética en " + temp);
        } finally {
            borrar(temp);
        }
    }

    private static void probarPublicacionCompleta(Path temp) throws Exception {
        Path destino = Files.createDirectory(temp.resolve("salida-completa"));
        ConfiguracionDomitec cfg = new ConfiguracionDomitec();
        cfg.calentamiento = 15.0;
        cfg.validar();
        EstudioPareado estudio = new EstudioPareado();
        for (int seed = 1; seed <= 100; seed++) {
            String firma = repetir('a', 64);
            for (int escenario = 0; escenario < 3; escenario++) {
                ComparacionEscenarios.Resultado resultado = new ComparacionEscenarios.Resultado(
                        seed, escenario, seed + escenario * 0.1, seed * 2.0 + escenario,
                        seed * 3.0 + escenario, 0.5 + escenario, seed * 10.0 + escenario,
                        seed + escenario * 4.0, seed * 5.0 + escenario, seed * 6.0 + escenario);
                RegistroCorrida registro = serieSintetica(seed, escenario);
                estudio.agregar(resultado, firma, registro.seriesCsv(seed, escenario),
                        cfg.calentamiento, cfg, destino.toString());
            }
        }

        requiere(estudio.isTerminado(), "el estudio quedó terminado");
        requiere(estudio.getCount() == 300, "acumuló 300 resultados");
        requiere(SesionEstudio.ultimoResultado != null
                && SesionEstudio.ultimoResultado.getTernasOrdenadas().size() == 100,
                "publicación final expone 100 ternas");
        requiere(SesionEstudio.progreso == 300 && !SesionEstudio.ejecutando,
                "la sesión cerró en progreso 300");

        Path paquete = Paths.get(estudio.getSalida());
        requiere(Files.isDirectory(paquete), "paquete publicado en directorio final");
        requiere(Files.isRegularFile(paquete.resolve("COMPLETO")), "marcador COMPLETO se publica al final");
        List<String> resultados = Files.readAllLines(paquete.resolve("resultados.csv"), StandardCharsets.UTF_8);
        List<String> series = Files.readAllLines(paquete.resolve("series_semanales.csv"), StandardCharsets.UTF_8);
        List<String> ics = Files.readAllLines(paquete.resolve("ic_pareados.csv"), StandardCharsets.UTF_8);
        String metadata=Files.readString(paquete.resolve("metadata.txt"),StandardCharsets.UTF_8);
        requiere(resultados.size() == 301, "CSV resultados: 301 filas con encabezado");
        requiere(resultados.get(0).equals("seed,escenario,firma_demanda,warmup_semanas,fillRate,backlog,stock,bw,produccion,canceladas,wip_max,insumos_final"),
                "CSV resultados incluye 3 métricas operativas finales");
        requiere(resultados.get(1).split(",", -1).length == 12, "resultados conserva 12 columnas por fila");
        requiere(series.size() == 30001, "CSV series: 30001 filas con encabezado");
        requiere(series.get(0).split(",", -1).length == 9 && series.get(1).split(",", -1).length == 9,
                "series semanales conserva sus 9 columnas");
        requiere(ics.size() == 16, "CSV IC: 16 filas con encabezado");
        requiere(metadata.contains("mejoraEscenario_hipotesis=1.0"), "metadata registra mejoraEscenario");
        requiere(metadata.contains("no constituyen validacion real en planta"), "metadata aclara que no es validación real");
        for (int i = 1; i < ics.size(); i++)
            requiere(ics.get(i).split(",", -1)[3].equals("100"), "cada IC publicado tiene n=100");
        SesionEstudio.ultimoResultado=null;
        SesionEstudio.leerUltimoEstudio(destino.toString());
        requiere(SesionEstudio.ultimoResultado.getCount()==300,"lee los CSV publicados en otra sesion");
        requiere(SesionEstudio.ultimoResultado.pairCI95(0,1,"bw").n==100,"IC recargado conserva 100 pares");
        ComparacionEscenarios.Resultado recargado=SesionEstudio.ultimoResultado.ternasOrdenadas().get(0);
        requiere(recargado.canceladas==1.0 && recargado.wipMax==5.0 && recargado.insumosFinal==6.0,
                "lectura nueva conserva las 3 métricas operativas");
        probarLecturaFormatoAnterior(destino, paquete, resultados);
        Path parcial=Files.createDirectory(destino.resolve("comparacion_99999999_incompleta"));
        Files.copy(paquete.resolve("resultados.csv"),parcial.resolve("resultados.csv"));
        SesionEstudio.leerUltimoEstudio(destino.toString());
        requiere(!SesionEstudio.estado.contains("99999999_incompleta"),"ignora paquetes sin marcador COMPLETO");
    }

    private static void probarLecturaFormatoAnterior(Path destino, Path paquete, List<String> filas) throws Exception {
        Path viejo=Files.createDirectory(destino.resolve("comparacion_zz_legacy"));
        StringBuilder csv=new StringBuilder("seed,escenario,firma_demanda,warmup_semanas,fillRate,backlog,stock,bw,produccion\n");
        for(int i=1;i<filas.size();i++) {
            String[] c=filas.get(i).split(",",-1);
            csv.append(String.join(",", java.util.Arrays.copyOf(c,9))).append('\n');
        }
        Files.writeString(viejo.resolve("resultados.csv"),csv.toString(),StandardCharsets.UTF_8);
        Files.writeString(viejo.resolve("COMPLETO"),"legacy\n",StandardCharsets.UTF_8);
        SesionEstudio.leerUltimoEstudio(destino.toString());
        ComparacionEscenarios.Resultado recargado=SesionEstudio.ultimoResultado.ternasOrdenadas().get(0);
        requiere(recargado.canceladas==0.0 && recargado.wipMax==0.0 && recargado.insumosFinal==0.0,
                "lectura antigua completa métricas nuevas con cero");
    }

    private static void probarReintentoExportacion(Path temp) throws Exception {
        ConfiguracionDomitec cfg = new ConfiguracionDomitec();
        cfg.validar();
        EstudioPareado estudio = new EstudioPareado();
        Path destinoValido = Files.createDirectory(temp.resolve("reintento-correcto"));
        Path destinoInvalido = Files.write(temp.resolve("destino-archivo"), new byte[] {1});
        try { cargarFixtures(estudio, cfg, destinoValido.toString(), destinoInvalido.toString()); }
        catch (RuntimeException esperado) { checks++; }
        requiere(estudio.getCount() == 300 && !estudio.isTerminado(), "fallo de publicación retiene las 300 corridas");
        requiere(estudio.getEstado().startsWith("Error:"), "fallo expone estado recuperable");
        estudio.reintentarExportacion(destinoValido.toString());
        requiere(estudio.isTerminado() && estudio.getCount() == 300, "reintento publica sin recomputar");
        Path paquete = Paths.get(estudio.getSalida());
        requiere(Files.isRegularFile(paquete.resolve("resultados.csv")), "reintento conserva resultados.csv");
        requiere(Files.isRegularFile(paquete.resolve("series_semanales.csv")), "reintento conserva series.csv");
        requiere(Files.isRegularFile(paquete.resolve("ic_pareados.csv")), "reintento conserva IC");
        requiere(Files.isRegularFile(paquete.resolve("metadata.txt")), "reintento conserva configuración y warmup");
        requiere(Files.isRegularFile(paquete.resolve("COMPLETO")), "reintento publica marcador final");
    }

    private static void cargarFixtures(EstudioPareado estudio, ConfiguracionDomitec cfg,
                                       String destino, String destinoFinal) {
        for (int seed = 1; seed <= 100; seed++) for (int escenario = 0; escenario < 3; escenario++) {
            ComparacionEscenarios.Resultado r = new ComparacionEscenarios.Resultado(seed, escenario,
                    seed + escenario * 0.1, seed * 2.0 + escenario, seed * 3.0 + escenario,
                    0.5 + escenario, seed * 10.0 + escenario, seed + escenario * 4.0,
                    seed * 5.0 + escenario, seed * 6.0 + escenario);
            RegistroCorrida registro = serieSintetica(seed, escenario);
            estudio.agregar(r, repetir('a', 64), registro.seriesCsv(seed, escenario),
                    cfg.calentamiento, cfg, seed == 100 && escenario == 2 ? destinoFinal : destino);
        }
    }

    private static void probarRechazos(Path temp) throws Exception {
        ConfiguracionDomitec cfg = new ConfiguracionDomitec();
        cfg.validar();
        Path destino = Files.createDirectory(temp.resolve("rechazos"));

        EstudioPareado semillaFueraOrden = new EstudioPareado();
        esperaFallo(new Accion() { public void run() {
            semillaFueraOrden.agregar(resultado(2,0), repetir('a',64), cabeceraSerie(),
                    cfg.calentamiento, cfg, destino.toString());
        }}, "rechaza semilla fuera de orden");

        EstudioPareado escenarioFueraOrden = new EstudioPareado();
        esperaFallo(new Accion() { public void run() {
            escenarioFueraOrden.agregar(resultado(1,1), repetir('a',64), cabeceraSerie(),
                    cfg.calentamiento, cfg, destino.toString());
        }}, "rechaza escenario fuera de orden");

        EstudioPareado firmasDistintas = new EstudioPareado();
        RegistroCorrida registro = serieSintetica(1, 0);
        firmasDistintas.agregar(resultado(1,0), repetir('a',64), registro.seriesCsv(1,0),
                cfg.calentamiento, cfg, destino.toString());
        registro = serieSintetica(1, 1);
        firmasDistintas.agregar(resultado(1,1), repetir('b',64), registro.seriesCsv(1,1),
                cfg.calentamiento, cfg, destino.toString());
        final EstudioPareado estudioFirma = firmasDistintas;
        final RegistroCorrida registroTercero = serieSintetica(1, 2);
        esperaFallo(new Accion() { public void run() {
            estudioFirma.agregar(resultado(1,2), repetir('a',64), registroTercero.seriesCsv(1,2),
                    cfg.calentamiento, cfg, destino.toString());
        }}, "rechaza firmas distintas en una terna");
    }

    private static RegistroCorrida serieSintetica(int seed, int escenario) {
        RegistroCorrida r = new RegistroCorrida();
        for (int semana = 0; semana < 100; semana++) {
            double base = seed + escenario + semana;
            r.semanal(semana, base, base + 1.0, base + 2.0, base + 3.0, base + 4.0, base + 5.0);
        }
        return r;
    }

    private static ComparacionEscenarios.Resultado resultado(int seed, int escenario) {
        return new ComparacionEscenarios.Resultado(seed, escenario, 0.8, 10, 20, 1, 30);
    }
    private static String cabeceraSerie() {
        return "seed,escenario,semana,demanda,ordenes,produccion,stock,backlog,wip\n0,0,0,0,0,0,0,0,0\n";
    }
    private static String repetir(char c, int n) {
        StringBuilder b = new StringBuilder(n); for (int i=0;i<n;i++) b.append(c); return b.toString();
    }
    private static void requiere(boolean condicion, String detalle) {
        if (!condicion) throw new AssertionError(detalle);
        checks++;
    }
    private interface Accion { void run(); }
    private static void esperaFallo(Accion a, String detalle) {
        try { a.run(); } catch (IllegalArgumentException | IllegalStateException esperado) { checks++; return; }
        throw new AssertionError(detalle);
    }
    private static void borrar(Path root) throws IOException {
        if (!Files.exists(root)) return;
        try (Stream<Path> paths = Files.walk(root)) {
            paths.sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
                try { Files.deleteIfExists(p); } catch (IOException e) { throw new RuntimeException(e); }
            });
        }
    }
}
