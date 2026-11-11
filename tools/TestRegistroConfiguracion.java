/** Pruebas autocontenidas para configuracion y registro, sin framework externo. */
public final class TestRegistroConfiguracion {
    private static int checks;
    public static void main(String[] args) {
        configuracion();
        registroFifoYVentanas();
        firmaYSeries();
        System.out.println("OK: " + checks + " comprobaciones de ConfiguracionDomitec/RegistroCorrida");
    }
    private static void configuracion() {
        ConfiguracionDomitec c=new ConfiguracionDomitec().validar();
        eq(DatosOperativos.medias()[0][0],c.medias[0][0],"media historica default");eq(0,c.medias[1][5],"media cero");
        eq(5,ConfiguracionDomitec.indice("detergente concentrado"),"indice por nombre");
        ConfiguracionDomitec copia=c.copiarDeep();copia.medias[0][0]=1;
        eq(DatosOperativos.medias()[0][0],c.medias[0][0],"copia profunda");
        ConfiguracionDomitec e2=c.escenario(2);
        eq(168,e2.horas,"calendario real en escenario 2");eq(1,e2.factLatigo,"factor escenario 2");
        eq(1.275,e2.mejoraEscenario,"hipotesis de rendimiento, sin horas ficticias");
        eq(1.275,e2.escenario(2).mejoraEscenario,"seleccion idempotente");
        boolean invalido=false;try{c.escenario(3);}catch(IllegalArgumentException ex){invalido=true;}
        ok(invalido,"rechaza escenario invalido");
        invalido=false;try{c.medias[0][0]=Double.NaN;c.validar();}catch(IllegalArgumentException ex){invalido=true;}
        ok(invalido,"validacion rechaza NaN");
    }
    private static void registroFifoYVentanas() {
        RegistroCorrida r=new RegistroCorrida();
        r.pedido(0,2,10,true);r.pedido(0,3,10,false);r.pedido(0,4,10,false);
        r.diferido(0,5,15);
        eq(0.75,r.fillRate(3),"fill rate pedido poswarmup FIFO");
        eq(1.0/3.0,r.fillInmediato(0),"fill inmediato");
        eq(20,r.demandaTotal(3),"demanda posterior warmup");
        r.semanal(0,1,2,3,4,5,6);r.semanal(1,3,4,5,6,7,8);r.semanal(2,5,6,7,8,9,10);
        eq(1.0,r.bw(1),"bullwhip por varianzas muestrales");
        eq(12,r.produccionTotal(1),"produccion semanal posterior warmup");
    }
    private static void firmaYSeries() {
        RegistroCorrida a=new RegistroCorrida(),b=new RegistroCorrida();
        a.entrada(1,0,2,12.5);a.entrada(0,1,1,7);
        b.entrada(0,1,1,7);b.entrada(1,0,2,12.5);
        ok(a.firmaDemanda().equals(b.firmaDemanda()),"firma independiente del orden de insercion");
        a.semanal(1,2,3,4,5,6,7);
        ok(a.seriesCsv(42,1).contains("42,1,1.0,2.0,3.0,4.0,5.0,6.0,7.0"),"CSV con columnas y metadatos");
        ok(a.firmaDemanda().length()==64,"firma SHA-256 hexadecimal");
    }
    private static void eq(double e,double v,String m){if(Double.doubleToLongBits(e)!=Double.doubleToLongBits(v))throw new AssertionError(m+": "+e+" != "+v);checks++;}
    private static void ok(boolean b,String m){if(!b)throw new AssertionError(m);checks++;}
}
