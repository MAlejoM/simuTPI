/** Estado compartido, de solo lectura para la interfaz, del estudio 100 x 3. */
public final class SesionEstudio {
    private SesionEstudio() { }

    /** Texto breve del estado actual; las vistas solo deben leerlo. */
    public static volatile String estado = "Inactivo";
    /** Corridas terminadas, de 0 a 300. */
    public static volatile int progreso = 0;
    public static volatile boolean ejecutando = false;
    /** Solicitud cooperativa; el runner solo debe comprobarla entre ternas. */
    public static volatile boolean cancelar = false;
    /** Último resumen completo de una terna seed x tres escenarios. */
    public static volatile String ultimoResumen = "";
    /** Último comparador completo; solo se reemplaza al publicar un lote exitoso. */
    public static volatile ComparacionEscenarios ultimoResultado = null;
    /** Copia inmutable por convenio de la configuración que lanzó el lote. */
    public static volatile ConfiguracionDomitec configuracionEnCurso = null;
    /** Destino base de los cuatro CSV publicados al terminar 300 corridas. */
    public static volatile String carpetaEnCurso = java.nio.file.Paths.get(
            System.getProperty("user.dir"), "resultados_domitec").toString();

    /** Reserva la sesión de forma atómica. Devuelve false si ya hay una activa. */
    public static synchronized boolean iniciar() {
        if (ejecutando) return false;
        ejecutando = true;
        cancelar = false;
        progreso = 0;
        estado = "Preparando comparación (0/300)";
        ultimoResumen = "";
        return true;
    }

    /** Cierra la sesión; error null/blank indica finalización normal. */
    public static synchronized void finalizar(String error) {
        ejecutando = false;
        if (error == null || error.trim().isEmpty()) {
            estado = "Completado (" + progreso + "/300)";
        } else if (error.toLowerCase(java.util.Locale.ROOT).contains("cancel")) {
            estado = error;
        } else {
            estado = "Error: " + error;
        }
    }

    /** Finaliza y publica el comparador completo en la misma sección sincronizada. */
    public static synchronized void finalizar(String error, ComparacionEscenarios resultado) {
        if (error == null || error.trim().isEmpty()) {
            if (resultado != null) ultimoResultado = resultado;
            ejecutando = false;
            estado = "Completado (" + progreso + "/300)";
        } else {
            finalizar(error);
        }
    }
}
