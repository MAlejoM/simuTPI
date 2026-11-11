/** Estado compartido, de solo lectura para la interfaz, del estudio 100 x 3. */
public final class SesionEstudio {
    private SesionEstudio() { }

    /** Texto breve del estado actual; las vistas solo deben leerlo. */
    public static volatile String estado = "Inactivo";
    /** Corridas terminadas, de 0 a 300. */
    public static volatile int progreso = 0;
    public static volatile boolean ejecutando = false;
    /** Solicitud cooperativa; el runner solo debe comprobarla entre ternas. */
    public static volatile boolean cancelar = false;
    /** Último resumen completo de una terna seed x tres escenarios. */
    public static volatile String ultimoResumen = "";
    /** Último comparador completo; solo se reemplaza al publicar un lote exitoso. */
    public static volatile ComparacionEscenarios ultimoResultado = null;
    /** Copia inmutable por convenio de la configuración que lanzó el lote. */
    public static volatile ConfiguracionDomitec configuracionEnCurso = null;
    /** Destino base de los cuatro CSV publicados al terminar 300 corridas. */
    public static volatile String carpetaEnCurso = java.nio.file.Paths.get(
            System.getProperty("user.dir"), "resultados_operativos_v2").toString();

    private static java.nio.file.Path archivoPreparacion() {
        return java.nio.file.Paths.get(System.getProperty("user.dir"), "domitec_estudio.properties").toAbsolutePath();
    }

    /** Persiste entradas comunes para el experimento que AnyLogic lanzará en otra JVM. */
    public static synchronized void preparar(ConfiguracionDomitec cfg, String carpeta) {
        cfg.validar();
        if(carpeta==null || carpeta.trim().isEmpty())throw new IllegalArgumentException("Elegir una carpeta de resultados");
        java.util.Properties p=new java.util.Properties();
        p.setProperty("version","2");p.setProperty("carpeta",java.nio.file.Paths.get(carpeta).toAbsolutePath().toString());
        for(int c=0;c<3;c++)for(int i=0;i<6;i++){
            p.setProperty("media."+c+"."+i,Double.toString(cfg.medias[c][i]));
            p.setProperty("desvio."+c+"."+i,Double.toString(cfg.desvios[c][i]));
        }
        for(int i=0;i<6;i++){
            p.setProperty("lead."+i,Double.toString(cfg.leadDias[i]));
            p.setProperty("cobertura."+i,Double.toString(cfg.cobertura[i]));
            p.setProperty("rate."+i,Double.toString(cfg.rate[i]));
        }
        p.setProperty("mermaLav",Double.toString(cfg.mermaLav));p.setProperty("mermaLiq",Double.toString(cfg.mermaLiq));
        p.setProperty("tiempos",Double.toString(cfg.tiemposFactor));p.setProperty("capacidad",Double.toString(cfg.capacidadFactor));
        p.setProperty("alfa",Double.toString(cfg.factLatigo));p.setProperty("horas",Double.toString(cfg.horas));
        p.setProperty("warmup",Double.toString(cfg.calentamiento));p.setProperty("reactores",Integer.toString(cfg.reactores));
        p.setProperty("cola",Integer.toString(cfg.cola));p.setProperty("tanque",Integer.toString(cfg.tanque));
        p.setProperty("esperaPedidoDias",Double.toString(cfg.esperaPedidoDias));
        p.setProperty("maxLotesEnProceso",Integer.toString(cfg.maxLotesEnProceso));
        p.setProperty("mejoraEscenario",Double.toString(cfg.mejoraEscenario));
        java.nio.file.Path target=archivoPreparacion(), temp=null;
        try {
            temp=java.nio.file.Files.createTempFile(target.getParent(),".domitec-estudio-",".tmp");
            try(java.io.Writer writer=java.nio.file.Files.newBufferedWriter(temp,java.nio.charset.StandardCharsets.UTF_8)){
                p.store(writer,"Entradas comunes de los tres escenarios; 100 semillas por escenario");
            }
            try{java.nio.file.Files.move(temp,target,java.nio.file.StandardCopyOption.ATOMIC_MOVE,java.nio.file.StandardCopyOption.REPLACE_EXISTING);}
            catch(java.nio.file.AtomicMoveNotSupportedException ex){java.nio.file.Files.move(temp,target,java.nio.file.StandardCopyOption.REPLACE_EXISTING);}
        }catch(java.io.IOException ex){throw new IllegalStateException("No se pudo guardar "+target,ex);}
        finally{if(temp!=null)try{java.nio.file.Files.deleteIfExists(temp);}catch(java.io.IOException ignored){}}
        configuracionEnCurso=cfg.copiarDeep();carpetaEnCurso=p.getProperty("carpeta");
        progreso=0;ultimoResultado=null;ultimoResumen="Entradas comunes guardadas";
        estado="Preparado: ejecutar Comparacion_100x3 desde el menu de AnyLogic";
    }

    /** Abrir y ejecutar la comparación directamente siempre permite usar defaults. */
    public static synchronized ConfiguracionDomitec configuracionPreparada() {
        if(configuracionEnCurso==null)usarPredeterminados();
        return configuracionEnCurso.copiarDeep();
    }

    public static synchronized void usarPredeterminados() {
        configuracionEnCurso=new ConfiguracionDomitec();
        carpetaEnCurso=java.nio.file.Paths.get(System.getProperty("user.dir"),"resultados_operativos_v2").toAbsolutePath().toString();
        progreso=0;ejecutando=false;cancelar=false;ultimoResultado=null;
        estado="Configuracion predeterminada | Listo para ejecutar";ultimoResumen="";
    }

    /** Solo se carga el archivo si el usuario elige expresamente esta opción. */
    public static synchronized void cargarConfiguracionGuardada() {
        ConfiguracionDomitec cfg=new ConfiguracionDomitec();
        java.nio.file.Path source=archivoPreparacion();
        if(!java.nio.file.Files.isRegularFile(source))throw new IllegalStateException("No hay configuracion guardada. Usar valores predeterminados o guardar parametros desde Main.");
        if(java.nio.file.Files.isRegularFile(source)) {
            java.util.Properties p=new java.util.Properties();
            try(java.io.Reader reader=java.nio.file.Files.newBufferedReader(source,java.nio.charset.StandardCharsets.UTF_8)){p.load(reader);}
            catch(java.io.IOException ex){throw new IllegalStateException("No se pudo leer "+source,ex);}
            if(!"2".equals(p.getProperty("version")))throw new IllegalStateException("Configuracion anterior a la correccion 24x5: volver a guardar parametros desde Main");
            for(int c=0;c<3;c++)for(int i=0;i<6;i++){
                cfg.medias[c][i]=valor(p,"media."+c+"."+i);cfg.desvios[c][i]=valor(p,"desvio."+c+"."+i);
            }
            for(int i=0;i<6;i++){cfg.leadDias[i]=valor(p,"lead."+i);cfg.cobertura[i]=valor(p,"cobertura."+i);cfg.rate[i]=valor(p,"rate."+i);}
            cfg.mermaLav=valor(p,"mermaLav");cfg.mermaLiq=valor(p,"mermaLiq");
            cfg.tiemposFactor=valor(p,"tiempos");cfg.capacidadFactor=valor(p,"capacidad");
            cfg.factLatigo=valor(p,"alfa");cfg.horas=valor(p,"horas");cfg.calentamiento=valor(p,"warmup");
            cfg.reactores=Integer.parseInt(p.getProperty("reactores"));cfg.cola=Integer.parseInt(p.getProperty("cola"));cfg.tanque=Integer.parseInt(p.getProperty("tanque"));
            cfg.esperaPedidoDias=valor(p,"esperaPedidoDias");cfg.maxLotesEnProceso=Integer.parseInt(p.getProperty("maxLotesEnProceso"));
            if(p.getProperty("mejoraEscenario")!=null)cfg.mejoraEscenario=valor(p,"mejoraEscenario");
            String folder=p.getProperty("carpeta");
            if(folder==null || folder.trim().isEmpty())throw new IllegalStateException("La configuracion no tiene carpeta de resultados");
            carpetaEnCurso=folder;
        }
        configuracionEnCurso=cfg.validar().copiarDeep();
        progreso=0;ejecutando=false;cancelar=false;ultimoResultado=null;
        estado="Configuracion guardada cargada | Listo para ejecutar";ultimoResumen="";
    }

    private static double valor(java.util.Properties p,String key){
        String value=p.getProperty(key);
        if(value==null)throw new IllegalStateException("Falta parametro "+key);
        return Double.parseDouble(value);
    }

    /** Permite volver a Main en otra JVM y leer los IC del estudio publicado. */
    public static synchronized void leerUltimoEstudio(String carpeta) {
        java.nio.file.Path base=java.nio.file.Paths.get(carpeta), latest;
        try(java.util.stream.Stream<java.nio.file.Path> paths=java.nio.file.Files.list(base)) {
            latest=paths.filter(p->p.getFileName().toString().startsWith("comparacion_")
                    && java.nio.file.Files.isRegularFile(p.resolve("resultados.csv"))
                    && java.nio.file.Files.isRegularFile(p.resolve("COMPLETO")))
                    .max(java.util.Comparator.comparing(p->p.getFileName().toString()))
                    .orElseThrow(()->new IllegalStateException("No hay estudios completos en "+base));
        }catch(java.io.IOException ex){throw new IllegalStateException("No se pudo abrir "+base,ex);}
        ComparacionEscenarios datos=new ComparacionEscenarios();
        java.util.Map<Integer,String> firmas=new java.util.HashMap<Integer,String>();
        Double warmup=null;
        try {
            java.util.List<String> rows=java.nio.file.Files.readAllLines(latest.resolve("resultados.csv"),java.nio.charset.StandardCharsets.UTF_8);
            String headerViejo="seed,escenario,firma_demanda,warmup_semanas,fillRate,backlog,stock,bw,produccion";
            String headerNuevo=headerViejo+",canceladas,wip_max,insumos_final";
            boolean nuevo=rows.size()==301 && rows.get(0).equals(headerNuevo);
            if(rows.size()!=301 || (!nuevo && !rows.get(0).equals(headerViejo)))
                throw new IllegalStateException("El estudio no contiene 300 resultados completos");
            for(int i=1;i<rows.size();i++){
                String[] cells=rows.get(i).split(",",-1);
                if(cells.length!=(nuevo?12:9))throw new IllegalStateException("Fila de resultados invalida: "+i);
                int seed=Integer.parseInt(cells[0]),scenario=Integer.parseInt(cells[1]);
                double corte=Double.parseDouble(cells[3]);
                if(!Double.isFinite(corte)||corte<0||corte>=100 || (warmup!=null&&Double.compare(warmup,corte)!=0))
                    throw new IllegalStateException("Los resultados deben compartir un calentamiento valido");
                warmup=corte;
                if(!cells[2].matches("[0-9a-fA-F]{64}"))throw new IllegalStateException("Firma invalida");
                String old=firmas.put(seed,cells[2]);
                if(old!=null&&!old.equals(cells[2]))throw new IllegalStateException("Demanda distinta en semilla "+seed);
                ComparacionEscenarios.Resultado resultado;
                if(nuevo)resultado=new ComparacionEscenarios.Resultado(seed,scenario,Double.parseDouble(cells[4]),Double.parseDouble(cells[5]),Double.parseDouble(cells[6]),Double.parseDouble(cells[7]),Double.parseDouble(cells[8]),Double.parseDouble(cells[9]),Double.parseDouble(cells[10]),Double.parseDouble(cells[11]));
                else resultado=new ComparacionEscenarios.Resultado(seed,scenario,Double.parseDouble(cells[4]),Double.parseDouble(cells[5]),Double.parseDouble(cells[6]),Double.parseDouble(cells[7]),Double.parseDouble(cells[8]));
                datos.agregar(resultado);
            }
        }catch(java.io.IOException ex){throw new IllegalStateException("No se pudo leer el estudio",ex);}
        if(datos.getTernasOrdenadas().size()!=100)throw new IllegalStateException("Se requieren 100 ternas completas");
        ultimoResultado=datos;progreso=300;estado="Resultados cargados: "+latest;ultimoResumen=estado;
    }

    /** Reserva la sesión de forma atómica. Devuelve false si ya hay una activa. */
    public static synchronized boolean iniciar() {
        if (ejecutando) return false;
        ejecutando = true;
        cancelar = false;
        progreso = 0;
        estado = "Preparando comparación (0/300)";
        ultimoResumen = "";
        return true;
    }

    /** Cierra la sesión; error null/blank indica finalización normal. */
    public static synchronized void finalizar(String error) {
        ejecutando = false;
        if (error == null || error.trim().isEmpty()) {
            estado = "Completado (" + progreso + "/300)";
        } else if (error.toLowerCase(java.util.Locale.ROOT).contains("cancel")) {
            estado = error;
        } else {
            estado = "Error: " + error;
        }
    }

    /** Finaliza y publica el comparador completo en la misma sección sincronizada. */
    public static synchronized void finalizar(String error, ComparacionEscenarios resultado) {
        if (error == null || error.trim().isEmpty()) {
            if (resultado != null) ultimoResultado = resultado;
            ejecutando = false;
            estado = "Completado (" + progreso + "/300)";
        } else {
            finalizar(error);
        }
    }
}
