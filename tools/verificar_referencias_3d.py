"""Check actual camera methods against sector bounds and the known top view.

Uses real AnyLogic Camera3D objects with a capturing viewport; no simulation
engine is started and this does not certify a native rendered frame.
"""
from pathlib import Path
import json, os, subprocess, xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
INSTALL=next(p for p in [Path(r'C:\Program Files\AnyLogic 8.9 Personal Learning Edition'), Path(r'D:\AnyLogic 8.9 Personal Learning Edition')] if p.is_dir())

def method(code,name):
    start=code.index('public void '+name+'(');opening=code.index('{',start);depth=0
    for pos in range(opening,len(code)):
        if code[pos]=='{':depth+=1
        elif code[pos]=='}':
            depth-=1
            if depth==0:return code[start:pos+1]
    raise ValueError(name)

def main():
    tree=E.parse(ROOT/'domitec_interactivo/Domitec_Interactivo.alp')
    agents={a.findtext('Name'):a for a in tree.findall('Model/ActiveObjectClasses/ActiveObjectClass')}
    code=agents['Main'].findtext('AdditionalClassCode')
    sectors=json.loads((ROOT/'tools/sectores_planta.json').read_text(encoding='utf8'))
    scene=agents['DomitecPlant'].find('Presentation/Level/Presentation')
    expected=[]
    for i,s in enumerate(sectors):
        x,y,w,h=s['area'];expected.append([x+w/2,y+h/2])
        marker=next(n for n in scene.findall('Rectangle') if n.findtext('Name')==f'guia_marca_{i}')
        mx,my,mw,mh=[float(marker.findtext(k)) for k in ['X','Y','Width','Height']]
        assert x<=mx and mx+mw<=x+w and y<=my and my+mh<=y+h,s['nombre']
        assert float(marker.findtext('Z'))>=100,s['nombre']
    expected_java='new double[][]{'+','.join('{'+str(x)+','+str(y)+'}' for x,y in expected)+'}'
    java='''import com.anylogic.engine.presentation.Camera3D;
public class TestReferencias3D {
    static class Viewport { Camera3D camera; void setCamera(Camera3D c,boolean follow,long ms){camera=c;} }
    Viewport ventanaPlanta3D=new Viewport();
    int sector3DActivo;
'''+ '\n'.join(method(code,name) for name in ['restablecerCamara','vistaSuperior','enfocarSector3D'])+'''
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    public static void main(String[] args){
        TestReferencias3D t=new TestReferencias3D();
        t.restablecerCamara();Camera3D initial=t.ventanaPlanta3D.camera;
        check(initial.getX()==920 && initial.getZ()==1300,"Same longitudinal center and height as top view");
        check(initial.getRotationX()==Math.toRadians(55) && initial.getRotationZ()==-Math.PI/2,"Side perspective orientation");
        double reach=initial.getZ()/Math.tan(initial.getRotationX());
        check(Math.abs(initial.getX()+reach*Math.cos(initial.getRotationZ())-920)<1e-8,"Perspective aims at plant center X");
        check(Math.abs(initial.getY()+reach*Math.sin(initial.getRotationZ())-605)<1e-8,"Perspective aims at plant center Y");
        t.vistaSuperior();Camera3D top=t.ventanaPlanta3D.camera;
        check(top.getX()==920 && top.getY()==605 && top.getZ()==1300 && top.getRotationX()==Math.PI/2,"Working top view preserved");
        double[][] expected='''+expected_java+''';
        for(int i=0;i<expected.length;i++){
            t.sector3DActivo=i;t.enfocarSector3D();Camera3D c=t.ventanaPlanta3D.camera;
            check(c.getX()==expected[i][0] && c.getY()==expected[i][1],"Sector target "+(i+1));
            check(c.getRotationX()==Math.PI/2 && c.getRotationZ()==0,"Top-down sector "+(i+1));
        }
        System.out.println("PASS: centered side perspective; top view and nine sector targets preserved");
    }
}'''
    work=ROOT/'tools/_workspace_referencias_3d';work.mkdir(exist_ok=True)
    source=work/'TestReferencias3D.java';source.write_text(java,encoding='utf8')
    build=Path.home()/'.AnyLogicPLE/Workspace8.8/Domitec_Interactivo_BUILD'
    cp=os.pathsep.join(e.get('path') for e in E.parse(build/'.classpath').findall('classpathentry') if e.get('kind')=='lib')
    subprocess.run([str(INSTALL/'jre/bin/javac.exe'),'-encoding','UTF-8','-cp',cp,'-d',str(work),str(source)],check=True)
    subprocess.run([str(INSTALL/'jre/bin/java.exe'),'-cp',str(work)+os.pathsep+cp,'TestReferencias3D'],check=True)

if __name__=='__main__':main()
