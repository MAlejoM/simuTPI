/** Material accounting in equivalent boxes. Raw stock is distinct from released WIP. */
public final class BalanceMateriales {
    public static final double LOTE = 1000;
    private final double[] recibido=new double[6], materiaPrima=new double[6], proceso=new double[6];
    private final double[] terminado=new double[6], rechazo=new double[6];
    private double picoWip;
    public void recibir(int p,double cajas){ validar(p,cajas);recibido[p]+=cajas;materiaPrima[p]+=cajas; }
    public double materiaPrima(int p){validar(p,0);return materiaPrima[p];}
    public double enProceso(int p){validar(p,0);return proceso[p];}
    public double wip(){double x=0;for(double q:proceso)x+=q;return x;}
    public double materiasPrimas(){double x=0;for(double q:materiaPrima)x+=q;return x;}
    public double picoWip(){return picoWip;}
    /** Returns false when the release card/buffer is occupied; never discards excess material. */
    public boolean liberar(int p,int maxPorProducto,int maxGlobal){
        validar(p,0);
        if(maxPorProducto<1||maxGlobal<1)throw new IllegalArgumentException("Limites de liberacion positivos");
        if(materiaPrima[p]<LOTE-1e-8 || proceso[p]+LOTE>maxPorProducto*LOTE+1e-8
                || wip()+LOTE>maxGlobal*LOTE+1e-8)return false;
        materiaPrima[p]-=LOTE;proceso[p]+=LOTE;picoWip=Math.max(picoWip,wip());return true;
    }
    public void finalizar(int p,double cajas,boolean scrap){
        validar(p,cajas);
        if(cajas>proceso[p]+1e-8)throw new IllegalStateException("Salida sin lote liberado: producto "+p);
        proceso[p]-=cajas;if(scrap)rechazo[p]+=cajas;else terminado[p]+=cajas;
    }
    /** Independent accounting identity, including material waiting outside the process. */
    public void verificar(){
        for(int p=0;p<6;p++)if(Math.abs(recibido[p]-materiaPrima[p]-proceso[p]-terminado[p]-rechazo[p])>1e-6)
            throw new IllegalStateException("No conserva material en producto "+p);
    }
    private static void validar(int p,double cajas){
        if(p<0||p>=6||!Double.isFinite(cajas)||cajas<0)throw new IllegalArgumentException("Producto/cantidad invalidos");
    }
}
