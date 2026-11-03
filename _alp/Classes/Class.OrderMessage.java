import java.io.Serializable;

public class OrderMessage implements Serializable {
    public ProductType product;
    public double amount;

    // Constructor
    public OrderMessage(ProductType product, double amount) {
        this.product = product;
        this.amount = amount;
    }
}