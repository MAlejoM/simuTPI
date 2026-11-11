public final class TestBalanceMateriales {
    public static void main(String[] args){
        BalanceMateriales b=new BalanceMateriales();
        b.recibir(0,800000);
        for(int i=0;i<800;i++)b.liberar(0,6,36);
        if(b.wip()!=6000||b.materiaPrima(0)!=794000)throw new AssertionError("800k receipt must remain accounted as raw stock");
        for(int p=1;p<6;p++){b.recibir(p,100000);for(int i=0;i<100;i++)b.liberar(p,6,36);}
        if(b.wip()!=36000)throw new AssertionError("global release bound");
        b.finalizar(0,1000,false);b.finalizar(1,1000,true);b.verificar();
        if(!b.liberar(0,6,36)||!b.liberar(1,6,36)||b.liberar(1,6,36))throw new AssertionError("return release cards");
        for(int i=0;i<1000;i++){
            int p=i%6;b.finalizar(p,1000,i%13==0);
            if(b.materiaPrima(p)<1000)b.recibir(p,1000);
            b.liberar(p,6,36);b.verificar();
            if(b.wip()>36000)throw new AssertionError();
        }
        boolean rejected=false;try{b.finalizar(0,10000000,false);}catch(IllegalStateException ex){rejected=true;}
        if(!rejected)throw new AssertionError("cannot finish nonexistent material");
        System.out.println("PASS: bounded release, 800k receipt conservation, scrap, 1000 material transfers");
    }
}
