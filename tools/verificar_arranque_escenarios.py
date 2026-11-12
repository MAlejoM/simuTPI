"""Regression: execute the exact serialized Main startup selection with each experiment's inputs."""
from pathlib import Path
import subprocess,xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
JAVA=next(p/'jre/bin' for p in [Path(r'C:\Program Files\AnyLogic 8.9 Personal Learning Edition'), Path(r'D:\AnyLogic 8.9 Personal Learning Edition')] if (p/'jre/bin/javac.exe').is_file())

def main():
    model=E.parse(ROOT/'domitec_interactivo/Domitec_Interactivo.alp').getroot().find('Model')
    agent=next(a for a in model.findall('ActiveObjectClasses/ActiveObjectClass') if a.findtext('Name')=='Main')
    body=agent.findtext('AdditionalClassCode')
    start=body.index('    cfg = configuracionInicial == null')
    end=body.index('    aplicarConfiguracion(cfg, false);',start)
    selection=body[start:end]
    cases=[]
    names=['Simulation_Escenario0_AsIs','Simulation_Escenario1_SinPanico','Simulation_Escenario2_Integral']
    for expected,name in enumerate(names):
        experiment=next(e for e in model.findall('Experiments/*') if e.findtext('Name')==name)
        inputs={p.findtext('ParameterName'):p.findtext('ParameterValue/Code') for p in experiment.findall('Parameters/Parameter')}
        assert inputs['numeroEscenario']==str(expected),(name,inputs)
        assert inputs['escalaTurnoMain']=='1.0' and inputs['esComparacion']=='false',name
        cases.append('''
        { Arranque a=new Arranque(); a.numeroEscenario=%s; a.factorLatigoMain=%s;
          a.iniciar();
          if(a.escenarioActivo!=%s || a.cfg.factLatigo!=%s || a.cfg.mejoraEscenario!=%s || a.cfg.horas!=168)
              throw new AssertionError("Wrong startup: %s");
          System.out.println("PASS: %s -> scenario "+a.escenarioActivo+", throughput factor "+a.cfg.mejoraEscenario);
        }
        '''%(inputs['numeroEscenario'],inputs['factorLatigoMain'],expected,
             '1.5' if expected==0 else '1.0','1.275' if expected==2 else '1.0',name,name))
    source='''public class TestArranqueSerializado {
      static class Arranque {
        ConfiguracionDomitec cfg=new ConfiguracionDomitec(),configuracionInicial;
        int numeroEscenario=-1,escenarioActivo;
        double factorLatigoMain;
        void iniciar(){ %s }
      }
      public static void main(String[] args){ %s }
    }'''%(selection,'\n'.join(cases))
    work=ROOT/'tools/_workspace_arranque_escenarios';work.mkdir(exist_ok=True)
    file=work/'TestArranqueSerializado.java';file.write_text(source,encoding='utf8')
    cp=[str(ROOT/'tools'/f'{n}.java') for n in ['ConfiguracionDomitec','DatosOperativos','ComparacionEscenarios']]
    p=subprocess.run([str(JAVA/'javac.exe'),'-encoding','UTF-8','-d',str(work),str(file),*cp],text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    p=subprocess.run([str(JAVA/'java.exe'),'-cp',str(work),'TestArranqueSerializado'],text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    print(p.stdout.strip())

if __name__=='__main__':main()
