import java.io.Serializable;

public class ProductState implements Serializable {
    public ProductType product;
    public double inventory;
    public double backlog; 
    public double weeklyCapacity; 
    public double onOrder; // NUEVO: Insumos que ya pedimos y están en viaje

    public ProductState(ProductType product, double initialInventory, double weeklyCapacity) {
        this.product = product;
        this.inventory = initialInventory;
        this.backlog = 0;
        this.weeklyCapacity = weeklyCapacity;
        this.onOrder = 0; // Arranca en 0
    }
}