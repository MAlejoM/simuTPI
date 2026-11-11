public final class TestCalendarioPlanta {
    static void cerca(double a,double b){if(Math.abs(a-b)>1e-8)throw new AssertionError(a+" != "+b);}
    public static void main(String[] args) {
        cerca(CalendarioPlanta.duracion(0,120,120,5)*168,120);
        cerca(CalendarioPlanta.duracion(119.0/168,2,120,5)*168,50);
        cerca(CalendarioPlanta.duracion(130.0/168,2,120,5)*168,40);
        cerca(CalendarioPlanta.duracion(0,240,120,5)*168,288);
        cerca(CalendarioPlanta.duracion(7.0/168,2,40,5)*168,18);
        if(!CalendarioPlanta.abierto(167.0/168,168)||!CalendarioPlanta.abierto(121.0/168,168))throw new AssertionError();
        cerca(CalendarioPlanta.duracion(119.0/168,200,168)*168,200);
        if(CalendarioPlanta.abierto(8.0/168,40,5))throw new AssertionError();
        for(int i=0;i<300;i++){
            double start=i/37.0, hours=0.3+i/13.0;
            double end=start+CalendarioPlanta.duracion(start,hours,120,5);
            if(end<start+hours/168.0-1e-9)throw new AssertionError();
            // Independently integrate the operating intervals intersected by [start,end].
            double work=0;
            for(int day=(int)Math.floor(start*7);day<=Math.floor(end*7);day++)if(day%7<5)
                work+=Math.max(0,Math.min(end*168,(day+1)*24)-Math.max(start*168,day*24));
            cerca(work,hours);
        }
        System.out.println("PASS: 24x7 clock, optional 24x5 closures, 300 independent work-hour integrals");
    }
}
