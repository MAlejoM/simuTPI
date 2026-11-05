import java.io.Serializable;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Deque;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/** Estadisticas por corrida sin dependencias del motor de simulacion. */
public final class RegistroCorrida implements Serializable {
    private static final long serialVersionUID = 1L;

    private static final class Cohorte implements Serializable {
        private static final long serialVersionUID = 1L;
        final int producto; final double tiempo, demanda;
        double cumplido, inmediato;
        Cohorte(int producto,double tiempo,double demanda) {
            this.producto=producto; this.tiempo=tiempo; this.demanda=demanda;
        }
        double pendiente() { return Math.max(0.0, demanda-cumplido); }
    }
    private static final class Semana implements Serializable {
        private static final long serialVersionUID = 1L;
        final double tiempo,demanda,ordenes,produccion,stock,backlog,wip;
        Semana(double t,double d,double o,double p,double s,double b,double w) {
            tiempo=t;demanda=d;ordenes=o;produccion=p;stock=s;backlog=b;wip=w;
        }
    }
    private static final class DemandaKey implements Comparable<DemandaKey>, Serializable {
        private static final long serialVersionUID = 1L;
        final String canal; final int producto; final long semana;
        DemandaKey(String c,int p,long s) { canal=c;producto=p;semana=s; }
        public int compareTo(DemandaKey x) {
            int c=canal.compareTo(x.canal); if(c!=0)return c;
            c=Integer.compare(producto,x.producto); return c!=0?c:Long.compare(semana,x.semana);
        }
    }

    private final List<Cohorte> cohortes = new ArrayList<Cohorte>();
    private final List<Semana> semanas = new ArrayList<Semana>();
    private final Map<Integer, Deque<Cohorte>> pendientes = new TreeMap<Integer, Deque<Cohorte>>();
    private final Map<DemandaKey, Double> entradas = new TreeMap<DemandaKey, Double>();

    /** Registra demanda. Si inmediato=true la cohorte se considera atendida al instante. */
    public void pedido(int producto, double tiempo, double cantidad, boolean inmediato) {
        validarProducto(producto); noNegativo("tiempo",tiempo); positivo("cantidad",cantidad);
        Cohorte c = new Cohorte(producto,tiempo,cantidad);
        cohortes.add(c);
        if (inmediato) { c.cumplido=cantidad; c.inmediato=cantidad; }
        else {
            Deque<Cohorte> q=pendientes.get(producto);
            if(q==null){q=new ArrayDeque<Cohorte>();pendientes.put(producto,q);}
            q.addLast(c);
        }
    }

    /** Satisface pedidos pendientes en orden FIFO por producto. El excedente se descarta. */
    public void diferido(int producto, double tiempo, double cantidad) {
        validarProducto(producto); noNegativo("tiempo",tiempo); noNegativo("cantidad",cantidad);
        double restante=cantidad;
        Deque<Cohorte> q=pendientes.get(producto);
        while(restante>0.0 && q!=null && !q.isEmpty()) {
            Cohorte c=q.peekFirst();
            double asignado=Math.min(restante,c.pendiente());
            c.cumplido+=asignado; restante-=asignado;
            if(c.pendiente()<=1e-12) q.removeFirst();
        }
    }

    public void produccion(double tiempo,double cantidad) {
        noNegativo("tiempo",tiempo);noNegativo("produccion",cantidad);
        // Produccion tambien puede registrarse como agregado independiente de la serie semanal.
        produccionEventos.add(new double[]{tiempo,cantidad});
    }

    private final List<double[]> produccionEventos = new ArrayList<double[]>();

    public void semanal(double tiempo,double demanda,double ordenes,double produccion,
                        double stock,double backlog,double wip) {
        noNegativo("tiempo",tiempo);noNegativo("demanda",demanda);noNegativo("ordenes",ordenes);
        noNegativo("produccion",produccion);noNegativo("stock",stock);
        noNegativo("backlog",backlog);noNegativo("wip",wip);
        semanas.add(new Semana(tiempo,demanda,ordenes,produccion,stock,backlog,wip));
    }

    /** Cantidad de tuplas semanales registradas. */
    public int numeroSemanas() { return semanas.size(); }

    /** Cantidad de claves canal/producto/semana unicas en la firma de demanda. */
    public int numeroEntradas() { return entradas.size(); }

    /** Fraccion de demanda posterior al warmup que fue finalmente satisfecha. */
    public double fillRate(double warmup) {
        noNegativo("warmup",warmup); double d=0,f=0;
        for(Cohorte c:cohortes) if(c.tiempo>=warmup){d+=c.demanda;f+=c.cumplido;}
        return d==0.0?0.0:f/d;
    }

    /** Fraccion de demanda posterior al warmup que se atendio al llegar. */
    public double fillInmediato(double warmup) {
        noNegativo("warmup",warmup); double d=0,f=0;
        for(Cohorte c:cohortes) if(c.tiempo>=warmup){d+=c.demanda;f+=c.inmediato;}
        return d==0.0?0.0:f/d;
    }

    public double demandaTotal(double warmup) {
        noNegativo("warmup",warmup);double total=0;
        for(Cohorte c:cohortes)if(c.tiempo>=warmup)total+=c.demanda;
        return total;
    }

    public double produccionTotal(double warmup) {
        noNegativo("warmup",warmup);double total=0;
        if(!produccionEventos.isEmpty()) {
            for(double[] e:produccionEventos)if(e[0]>=warmup)total+=e[1];
        } else {
            for(Semana s:semanas)if(s.tiempo>=warmup)total+=s.produccion;
        }
        return total;
    }

    /** Bullwhip = varianza muestral semanal de ordenes / varianza de demanda. */
    public double bw(double warmup) {
        noNegativo("warmup",warmup);List<Semana> xs=semanasTras(warmup);
        if(xs.size()<2)return 0.0;
        double vo=varianza(xs,true),vd=varianza(xs,false);
        return vd==0.0?0.0:vo/vd;
    }

    /** Registra la demanda base keyed; entradas repetidas de la misma clave se acumulan. */
    public void entrada(int canal,int producto,long semana,double cantidad) {
        entrada(Integer.toString(canal),producto,semana,cantidad);
    }
    public void entrada(String canal,int producto,long semana,double cantidad) {
        if(canal==null)throw new IllegalArgumentException("canal null");
        validarProducto(producto);noNegativo("semana",semana);noNegativo("cantidad",cantidad);
        DemandaKey key=new DemandaKey(canal,producto,semana);
        Double anterior=entradas.get(key);entradas.put(key,(anterior==null?0.0:anterior)+cantidad);
    }

    /** SHA-256 del CSV canonico, ordenado por canal, producto y semana. */
    public String firmaDemanda() {
        StringBuilder canon=new StringBuilder("canal,producto,semana,cantidad\n");
        for(Map.Entry<DemandaKey,Double> e:entradas.entrySet()) {
            DemandaKey k=e.getKey();
            canon.append(k.canal).append(',').append(k.producto).append(',').append(k.semana).append(',')
                    .append(Double.toString(e.getValue())).append('\n');
        }
        try {
            byte[] hash=MessageDigest.getInstance("SHA-256").digest(canon.toString().getBytes(StandardCharsets.UTF_8));
            StringBuilder hex=new StringBuilder(hash.length*2);
            for(byte b:hash)hex.append(String.format("%02x",b&0xff));
            return hex.toString();
        } catch(NoSuchAlgorithmException impossible) { throw new IllegalStateException("JRE sin SHA-256",impossible); }
    }

    public String seriesCsv(int seed,int escenario) {
        StringBuilder b=new StringBuilder("seed,escenario,semana,demanda,ordenes,produccion,stock,backlog,wip\n");
        List<Semana> xs=new ArrayList<Semana>(semanas);
        Collections.sort(xs,new Comparator<Semana>() { public int compare(Semana a,Semana z){return Double.compare(a.tiempo,z.tiempo);} });
        for(Semana s:xs)b.append(seed).append(',').append(escenario).append(',').append(s.tiempo).append(',')
                .append(s.demanda).append(',').append(s.ordenes).append(',').append(s.produccion).append(',')
                .append(s.stock).append(',').append(s.backlog).append(',').append(s.wip).append('\n');
        return b.toString();
    }

    public String resumen() {
        StringBuilder b=new StringBuilder("Cohortes: ").append(cohortes.size()).append("; semanas: ")
                .append(semanas.size()).append("; firmaDemanda: ").append(firmaDemanda()).append('\n');
        b.append("fillRate=").append(fillRate(0)).append("; fillInmediato=").append(fillInmediato(0))
                .append("; demanda=").append(demandaTotal(0)).append("; produccion=").append(produccionTotal(0))
                .append("; bw=").append(bw(0));
        return b.toString();
    }

    private List<Semana> semanasTras(double warmup){
        List<Semana> xs=new ArrayList<Semana>();for(Semana s:semanas)if(s.tiempo>=warmup)xs.add(s);return xs;
    }
    private static double varianza(List<Semana> xs,boolean ordenes){
        double media=0;for(Semana s:xs)media+=(ordenes?s.ordenes:s.demanda);media/=xs.size();
        double suma=0;for(Semana s:xs){double v=ordenes?s.ordenes:s.demanda;suma+=(v-media)*(v-media);}
        return suma/(xs.size()-1);
    }
    private static void validarProducto(int p){if(p<0||p>=6)throw new IllegalArgumentException("producto debe ser indice 0..5");}
    private static void noNegativo(String n,double x){if(Double.isNaN(x)||Double.isInfinite(x)||x<0)throw new IllegalArgumentException(n+" debe ser finito y >= 0");}
    private static void positivo(String n,double x){noNegativo(n,x);if(x==0)throw new IllegalArgumentException(n+" debe ser > 0");}
}
