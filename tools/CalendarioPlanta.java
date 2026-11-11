/** Working-time clock: default 24x7; model unit is week. */
public final class CalendarioPlanta {
    private CalendarioPlanta() {}
    public static boolean abierto(double semana, double horasSemanales) {
        return abierto(semana,horasSemanales,7);
    }
    public static boolean abierto(double semana, double horasSemanales,int diasSemanales) {
        validar(semana, 0, horasSemanales,diasSemanales);
        double hora = semana * 168.0;
        int dia = (int)Math.floor((hora % 168.0) / 24.0);
        return dia < diasSemanales && hora % 24.0 < horasSemanales / diasSemanales - 1e-9;
    }
    /** Elapsed calendar weeks needed to perform productive hours, skipping closures. */
    public static double duracion(double inicio, double horasTrabajo, double horasSemanales) {
        return duracion(inicio,horasTrabajo,horasSemanales,7);
    }
    public static double duracion(double inicio,double horasTrabajo,double horasSemanales,int diasSemanales) {
        validar(inicio, horasTrabajo, horasSemanales,diasSemanales);
        if (horasTrabajo == 0) return 0;
        double actual = inicio * 168.0, restante = horasTrabajo;
        double jornada = horasSemanales / diasSemanales;
        while (restante > 1e-9) {
            double semana = Math.floor((actual + 1e-9) / 168.0);
            double dentro = actual - semana * 168.0;
            int dia = (int)Math.floor((dentro + 1e-9) / 24.0);
            if (dia >= diasSemanales) { actual = (semana + 1) * 168.0; continue; }
            double horaDia = dentro - dia * 24.0;
            double disponible = jornada - horaDia;
            if (disponible <= 1e-9) { actual = semana * 168.0 + (dia + 1) * 24.0; continue; }
            double usado = Math.min(restante, disponible);
            actual += usado; restante -= usado;
        }
        return (actual - inicio * 168.0) / 168.0;
    }
    private static void validar(double inicio, double trabajo, double horas,int dias) {
        if (!Double.isFinite(inicio) || inicio < 0 || !Double.isFinite(trabajo) || trabajo < 0
                || dias<1||dias>7||!Double.isFinite(horas) || horas <= 0 || horas > dias*24)
            throw new IllegalArgumentException("Calendario: inicio/trabajo >= 0; horas semanales <= dias*24");
    }
}
