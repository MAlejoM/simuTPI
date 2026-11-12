"""Exercise the exact tab method with real AnyLogic shapes, without an Engine.

This verifies construction, immutable draw modes and visibility transitions.
It does not validate the rendered plant or run the simulation.
"""
from pathlib import Path
import os, subprocess, xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
INSTALL = next(p for p in [Path(r'C:\Program Files\AnyLogic 8.9 Personal Learning Edition'), Path(r'D:\AnyLogic 8.9 Personal Learning Edition')] if p.is_dir())
BUILD = Path.home()/'.AnyLogicPLE/Workspace8.8/Domitec_Interactivo_BUILD'

def main():
    tree = E.parse(ROOT/'domitec_interactivo/Domitec_Interactivo.alp')
    agent = next(a for a in tree.findall('Model/ActiveObjectClasses/ActiveObjectClass')
                 if a.findtext('Name') == 'Main')
    body = agent.findtext('AdditionalClassCode')
    method = body[body.index('public void mostrarVista('):body.index('public void elegirEscenario(')]
    assert '.setDrawMode(' not in method
    # Read the actual constructor statements and transforms from the model too.
    setup = body[body.index('    nivelPlanta3D = new '):body.index('    seleccionarPerfil(0, 0);')]
    java = '''import com.anylogic.engine.*;
import com.anylogic.engine.presentation.*;
public class TestVistasFijas extends Agent {
    ShapeTopLevelPresentationGroup presentation=new ShapeTopLevelPresentationGroup(this,true,0,0,0,0);
    ShapeEmbeddedObjectPresentation vistaPlanta3D;
    com.anylogic.engine.markup.Level nivelPlanta3D;
    TestVistasFijas domitecPlant;
    int vistaActiva;
    public ShapeTopLevelPresentationGroup getPresentationShape(){return presentation;}
''' + method[:method.index('public double stockProducto(')] + '\nvoid crearVistas(){\n' + setup + '''}
    public static void main(String[] args){
        TestVistasFijas main=new TestVistasFijas();
        main.domitecPlant=new TestVistasFijas();
        main.crearVistas();
        if(main.vistaPlanta3D.getLevel()!=main.nivelPlanta3D)
            throw new AssertionError("La planta debe estar registrada en un nivel 3D");
        if(!main.nivelPlanta3D.getShapes().contains(main.vistaPlanta3D)
            || !main.presentation.getShapes().contains(main.vistaPlanta3D))
            throw new AssertionError("La planta debe pertenecer al nivel y a la presentacion");
        for(int j=0;j<10;j++) for(int i=0;i<4;i++){
            main.mostrarVista(i);
            if(main.vistaPlanta3D.getDrawMode()!=SHAPE_DRAW_3D)
                throw new AssertionError("El modo debe permanecer fijo");
            if(main.vistaPlanta3D.isVisible()!=(i==0))
                throw new AssertionError("Visibilidad incorrecta");
        }
        System.out.println("PASS: 40 tab transitions with real AnyLogic shapes; no simulation engine");
    }
}'''
    work = ROOT/'tools/_workspace_vistas_fijas'
    work.mkdir(exist_ok=True)
    source = work/'TestVistasFijas.java'
    source.write_text(java,encoding='utf8')
    cp = os.pathsep.join(e.get('path') for e in E.parse(BUILD/'.classpath').findall('classpathentry')
                         if e.get('kind')=='lib')
    subprocess.run([str(INSTALL/'jre/bin/javac.exe'),'-encoding','UTF-8','-cp',cp,'-d',str(work),str(source)],check=True)
    subprocess.run([str(INSTALL/'jre/bin/java.exe'),'-cp',str(work)+os.pathsep+cp,'TestVistasFijas'],check=True)

if __name__ == '__main__': main()
