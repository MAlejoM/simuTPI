/** Quiet presentation routes; never consume RNG or alter production capacity. */
public final class OperarioAnimation {
    private OperarioAnimation() {}
    private static final double MINUTES_PER_WEEK = 7 * 24 * 60;
    private static final double CYCLE = MINUTES_PER_WEEK;
    private static final double OUT_START = 7200;
    private static final double OUT_END = 7380;
    private static final double BACK_START = 7800;
    private static final double BACK_END = 7980;
    private static final double DISTANCE_FACTOR = 0.25;

    private static double phase(double time, int person) {
        return ((time * MINUTES_PER_WEEK + person * 3100) % CYCLE + CYCLE) % CYCLE;
    }
    public static double progress(double time, int person) {
        double p = phase(time, person);
        if (p < OUT_START) return 0;
        if (p < OUT_END) return (p - OUT_START) / (OUT_END - OUT_START);
        if (p < BACK_START) return 1;
        if (p < BACK_END) return (BACK_END - p) / (BACK_END - BACK_START);
        return 0;
    }
    public static boolean walking(double time, int person) {
        double p = phase(time, person);
        return (p >= OUT_START && p < OUT_END) || (p >= BACK_START && p < BACK_END);
    }
    public static double coordinate(double time, int person, double origin, double delta) {
        return origin + DISTANCE_FACTOR * delta * progress(time, person);
    }
    public static double rotation(double time, int person, double dx, double dy) {
        double p = phase(time, person);
        return Math.atan2(dy, dx) + (p >= BACK_START && p < BACK_END ? Math.PI : 0);
    }
    public static String pose(double time, int person) {
        if (!walking(time, person)) return "idle";
        return ((long)Math.floor(time * MINUTES_PER_WEEK / 12.0) & 1L) == 0
                ? "walk_left" : "walk_right";
    }
}
