import java.io.Serializable;

public class DeliveryMessage implements Serializable {
    public ProductType product;
    public double amount;

    // Constructor
    public DeliveryMessage(ProductType product, double amount) {
        this.product = product;
        this.amount = amount;
    }
}