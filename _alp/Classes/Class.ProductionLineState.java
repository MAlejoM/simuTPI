import java.io.Serializable;

// Flujo de cajas equivalentes en seis máquinas y seis tramos de traslado.
// Todos los tiempos de traslado y disponibilidad son supuestos explícitos.
public class ProductionLineState implements Serializable {
    public ProductType product;
    public double[] queue = new double[6];
    public double[][] transit = new double[6][4]; // 4 intervalos de 15 min = 1 h
    public int[] repairTicks = new int[6];
    public double[] processed = new double[6];
    public double finished = 0;
    public double arrivals = 0;
    public double failures = 0;

    public ProductionLineState(ProductType product) {
        this.product = product;
    }

    public double wip() {
        double result = 0;
        for (int s = 0; s < 6; s++) {
            result += queue[s];
            for (int k = 0; k < 4; k++) result += transit[s][k];
        }
        return result;
    }
}