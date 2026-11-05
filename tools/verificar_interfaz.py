"""Check the serialized interactive model and compile its exact Java actions.

This is a compatibility/unit check, not a substitute for an AnyLogic run.
"""
from pathlib import Path
import json, os, subprocess, tempfile, zipfile
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'domitec_interactivo/Domitec_Interactivo.alp'
INSTALL=Path(r'D:\AnyLogic 8.9 Personal Learning Edition')

def main():
    t=E.parse(FILE);model=t.find('Model')
    agents={a.findtext('Name'):a for a in model.findall('ActiveObjectClasses/ActiveObjectClass')}
    main=agents['Main'];plant=agents['DomitecPlant']
    assert model.findtext('ModelTimeUnit')=='Week'
    for e in model.findall('Experiments/*'):
        assert e.findtext('ModelTimeProperties/InitialTime') in ['0','0.0']
        assert float(e.findtext('ModelTimeProperties/FinalTime'))==100
    study=next(e for e in model.findall('Experiments/*') if e.findtext('Name')=='Comparacion_100x3')
    assert study.tag=='ParamVariationExperiment'
    assert study.findtext('NumberOfRuns')=='100' and study.findtext('ReplicationsProperties/ReplicationPerIteration')=='3'
    assert study.findtext('AllowParallelEvaluations')=='false'
    ids={v.findtext('Name'):v.findtext('Id') for v in main.findall('Variables/Variable')}
    values={p.findtext('Id'):p.findtext('Expression/Code') for p in study.findall('FreeformParamValue')}
    assert values[ids['semillaReplica']]=='getCurrentIteration()'
    assert values[ids['numeroEscenario']]=='getCurrentReplication()-1'
    assert study.findtext('CustomGeneratorCode')=='new Random(getCurrentIteration())'
    assert {(seed,s) for seed in range(1,101) for s in range(3)}=={(i,r-1) for i in range(1,101) for r in range(1,4)}
    assert len(main.findall('.//Control[@Type="Window3D"]'))==1
    assert not plant.findall('.//Control')
    assert len([n for n in main.findall('.//Group') if n.findtext('Name','').startswith('cuerpoVista')])==4
    assert 'normal(' not in agents['Client'].findtext('Events/Event/Action')
    assert 'demandaComun' in agents['Client'].findtext('Events/Event/Action')
    assert 'observarSemana();' in main.findtext('Events/Event/Action')
    ui_code=main.findtext('AdditionalClassCode')
    assert '.setDrawMode(' not in ui_code, 'AnyLogic draw mode is fixed at construction'
    assert 'this, SHAPE_DRAW_2D, false' not in ui_code
    assert 'this, SHAPE_DRAW_3D, false' in ui_code
    assert 'vistaPlanta3D.setVisible(vista == 1)' in ui_code
    assert 'setRealTimeScale' not in plant.findtext('AgentProperties/OnReceive')
    for a in agents.values():
        for tag in ['Variables','Ports','Connectors','Events','AnalysisData','DynamicEvents']:
            for n in a.findall(tag+'/*'):
                assert n.findtext('PresentationFlag')=='false',(a.findtext('Name'),tag,n.findtext('Name'))
    for n in main.findall('EmbeddedObjects/EmbeddedObject'):
        assert float(n.findtext('X'))>=1500
    assert len([n for n in main.findall('.//Text') if n.findtext('Name','').startswith('planoLote')])==30
    for b in plant.findall('EmbeddedObjects/EmbeddedObject'):
        for generic in b.findall('GenericParameterSubstitute'):
            assert generic.findtext('GenericParameterSubstituteValue/Code')=='Batch',b.findtext('Name')
    for a in agents.values():
        scene=a.find('Presentation/Level/Presentation')
        if scene is not None:
            shape_ids=[n.text for n in scene.findall('.//Id')]
            assert len(shape_ids)==len(set(shape_ids)),a.findtext('Name')
    for n in t.findall('.//ResourceReference/ClassName'):
        if n.text and n.text.startswith('3d/'):assert (FILE.parent/n.text).is_file(),n.text
    print('PASS: 100 seeds x 3 scenarios, horizon 100 weeks, PLE-compatible experiment, four tabs, complete resources')

    # Use the real, previously generated class API to type-check all changed
    # methods/properties; cached binaries are copied into the temporary workspace.
    native=Path.home()/'.AnyLogicPLE/Workspace8.8/Domitec_Main_3D_BUILD/classes'
    imports='''package domitec_interactivo;
import com.anylogic.engine.*;import com.anylogic.engine.presentation.*;
import com.anylogic.libraries.processmodeling.*;
import domitec_main_3d.*;import domitec_main_3d.ProductType;import domitec_main_3d.ProductState;
'''
    work=ROOT/'tools/_workspace_interfaz_verificacion';work.mkdir(exist_ok=True)
    if (native/'domitec_main_3d/Main.class').is_file():
        with zipfile.ZipFile(work/'native.jar','w',zipfile.ZIP_DEFLATED) as z:
            for p in native.rglob('*.class'):z.write(p,p.relative_to(native))
    else:
        assert (work/'native.jar').is_file(), 'Open/build Domitec_Main_3D once to provide its native API, or run verificar_java_generado.py on the new model instead'
    with zipfile.ZipFile(work/'native.jar') as z:
        assert 'domitec_main_3d/Main.class' in z.namelist()
    jmain=imports+'public class Main extends domitec_main_3d.Main {\n'
    old_vars=set(['demandaHistorica','ordenesHistoricas','demandaSemanalActual','ordenesSemanalActual','produccionSemanalActual','produccionAnteriorGrafico','factorLatigoMain','escalaTurnoMain','lblFillRate','lblBacklog','lblSemana','lblEscenarioActual','barraGaugeFillRate','dsDemanda','dsOrdenes','dsProduccionSemanal','dsBacklog','dsWip'])
    for v in main.findall('Variables/Variable'):
        name=v.findtext('Name')
        if name not in old_vars:jmain+='public '+v.findtext('Properties/Type')+' '+name+';\n'
    for c in main.findall('.//Control'):
        if c.get('Type')=='EditBox':jmain+='public ShapeTextField '+c.findtext('Name')+';\n'
    jmain+=main.findtext('AdditionalClassCode')+'\n'
    types={'TextCode':'String','VisibleCode':'boolean','XCode':'double','YCode':'double','WidthCode':'double','FillColorCode':'java.awt.Color'}
    for i,n in enumerate(main.findall('Presentation/Level/Presentation//*')):
        if n.tag in types and n.text:jmain+=f'{types[n.tag]} property{i}(){{return {n.text};}}\n'
    for i,n in enumerate(main.findall('.//Control/BasicProperties/ActionCode')):jmain+=f'void action{i}(){{{n.text}}}\n'
    jmain+='}\n'
    jplant=imports+'public class DomitecPlant extends domitec_main_3d.DomitecPlant {\n@Override public Main get_Main(){return null;}\n'+plant.findtext('AdditionalClassCode')+'\n'
    jplant+='void receipt(Object msg){'+plant.findtext('AgentProperties/OnReceive')+'}\n'
    for i,b in enumerate(plant.findall('EmbeddedObjects/EmbeddedObject')):
        pars={p.findtext('Name'):p.findtext('Value/Code','') for p in b.findall('Parameters/Parameter')}
        for key in ['onEnter','onExit']:
            if pars.get(key):jplant+=f'void action{i}_{key}(Batch agent){{{pars[key]}}}\n'
        for key,kind in [('delayTime','double'),('newEntity','Batch'),('condition','boolean')]:
            if pars.get(key):jplant+=f'{kind} value{i}_{key}(Batch agent){{return {pars[key]};}}\n'
    for event in plant.findall('Events/Event'):
        if event.findtext('ExcludeFromBuild')!='true':jplant+='void weekly(){'+event.findtext('Action')+'}\n'
    jplant+='}\n'
    jclient=imports+'public class Client extends domitec_main_3d.Client {\n@Override public Main get_Main(){return null;}\nvoid demand(){'+agents['Client'].findtext('Events/Event/Action')+'}\n}'
    jsupplier=imports+'public class Supplier extends domitec_main_3d.Supplier {\n@Override public Main get_Main(){return null;}\nvoid receipt(Object msg){'+agents['Supplier'].findtext('AgentProperties/OnReceive')+'}\n}'
    jbatch=imports+'public class Batch extends domitec_main_3d.Batch {public long indiceCRN;public Batch(ProductType t,double q){super(t,q);}}'
    jstudy=imports+'public class Comparacion_100x3 extends domitec_main_3d.ParametersVariation {\n'+study.findtext('AdditionalClassCode')+'\nvoid after(Main root){'+study.findtext('AfterSimulationRunCode')+'}\n'
    for i,p in enumerate(study.findall('FreeformParamValue')):
        expr=p.findtext('Expression/Code')
        if not expr:continue
        name=next((name for name,uid in ids.items() if uid==p.findtext('Id')),None)
        if name:
            var=next(v for v in main.findall('Variables/Variable') if v.findtext('Name')==name)
            jstudy+=var.findtext('Properties/Type')+f' expr{i}(){{return {expr};}}\n'
    jstudy+='}'
    for name,source in [('Main',jmain),('DomitecPlant',jplant),('Client',jclient),('Supplier',jsupplier),('Batch',jbatch),('Comparacion_100x3',jstudy)]:
        (work/(name+'.java')).write_text(source,encoding='utf8')
    for cls in model.findall('JavaClasses/JavaClass'):
        if cls.findtext('Name') in ['ComparacionEscenarios','ConfiguracionDomitec','RegistroCorrida','SesionEstudio','EstudioPareado']:
            (work/(cls.findtext('Name')+'.java')).write_text('package domitec_interactivo;\n'+cls.findtext('Text'),encoding='utf8')
    cp=[work/'native.jar']
    for plugin,jar in [('com.anylogic.engine','com.anylogic.engine.jar'),('com.anylogic.engine.datautil','com.anylogic.engine.datautil.jar'),('com.anylogic.engine.database','com.anylogic.engine.database.jar'),('com.anylogic.process_modeling_library','lib/ProcessModelingLibrary.jar')]:cp.append(next((INSTALL/'plugins').glob(plugin+'_*'))/jar)
    p=subprocess.run([str(INSTALL/'jre/bin/javac.exe'),'-encoding','UTF-8','-Xmaxerrs','10','-cp',os.pathsep.join(map(str,cp)),'-d',str(work/'classes'),*[str(f) for f in work.glob('*.java')]],text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    print('PASS: exact UI methods, expressions, controls, event actions, stochastic properties and paired experiment actions compile against AnyLogic API')
    (FILE.parent/'verificacion_interfaz.json').write_text(json.dumps({'structure':'passed','java_action_compatibility':'passed','native_300_run':'not_performed','native_visual_validation':'pending_retest_after_layout_cleanup','delivery_speed_override':'removed','logic_element_presentation':'hidden','view_2d':'native_flow_diagram'},indent=2),encoding='utf8')

if __name__=='__main__':main()
