import java.nio.file.*;

/** Verifica persistencia de entradas comunes sin iniciar el runtime de AnyLogic. */
public final class TestPreparacionEstudio {
    public static void main(String[] args) throws Exception {
        Path temp=Files.createTempDirectory("domitec-config-test-");
        String previous=System.getProperty("user.dir");
        try {
            System.setProperty("user.dir",temp.toString());
            ConfiguracionDomitec cfg=new ConfiguracionDomitec();
            cfg.medias[2][4]=1234.5;cfg.desvios[0][1]=456.7;cfg.leadDias[3]=12;
            cfg.cobertura[1]=3.25;cfg.rate[5]=99;cfg.mermaLav=.12;cfg.mermaLiq=.23;
            cfg.capacidadFactor=1.2;cfg.tiemposFactor=.9;cfg.factLatigo=1.1;cfg.horas=45;
            cfg.calentamiento=17;cfg.reactores=7;cfg.cola=21;cfg.tanque=5;
            SesionEstudio.preparar(cfg,temp.resolve("salida").toString());
            // Clear process-local state to exercise the path used by a new JVM.
            SesionEstudio.configuracionEnCurso=null;SesionEstudio.carpetaEnCurso="";
            check(SesionEstudio.configuracionPreparada().medias[2][4]!=1234.5,"directo usa predeterminados, no archivo anterior");
            SesionEstudio.cargarConfiguracionGuardada();
            ConfiguracionDomitec loaded=SesionEstudio.configuracionPreparada();
            check(loaded.medias[2][4]==1234.5 && loaded.desvios[0][1]==456.7,"demanda");
            check(loaded.leadDias[3]==12 && loaded.cobertura[1]==3.25 && loaded.rate[5]==99,"inventario");
            check(loaded.mermaLav==.12 && loaded.mermaLiq==.23 && loaded.capacidadFactor==1.2 && loaded.tiemposFactor==.9,"proceso");
            check(loaded.factLatigo==1.1 && loaded.horas==45 && loaded.calentamiento==17,"politica");
            check(loaded.reactores==7 && loaded.cola==21 && loaded.tanque==5,"capacidades");
            check(SesionEstudio.carpetaEnCurso.equals(temp.resolve("salida").toString()),"carpeta");
            loaded.medias[2][4]=0;
            check(SesionEstudio.configuracionPreparada().medias[2][4]==1234.5,"copia independiente");
            Files.writeString(temp.resolve("domitec_estudio.properties"),"version=99\n");
            SesionEstudio.configuracionEnCurso=null;
            boolean rejected=false;
            try{SesionEstudio.cargarConfiguracionGuardada();}catch(IllegalStateException expected){rejected=true;}
            check(rejected,"rechaza formato desconocido");
            System.out.println("PASS: 9 preparation/reload checks; no AnyLogic runtime launched");
        } finally {
            System.setProperty("user.dir",previous);
            try(java.util.stream.Stream<Path> paths=Files.walk(temp)){
                for(Path p:(Iterable<Path>)paths.sorted(java.util.Comparator.reverseOrder())::iterator)Files.delete(p);
            }
        }
    }
    private static void check(boolean valid,String message){if(!valid)throw new AssertionError(message);}
}
