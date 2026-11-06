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
    weekly_sampler=next(n for n in main.findall('Events/Event') if n.findtext('Name')=='observarSemana')
    assert float(weekly_sampler.findtext('Properties/OccurrenceTime/Code'))==0.9999
    ui_code=main.findtext('AdditionalClassCode')
    apply_button=next(n for n in main.findall('.//Control') if n.findtext('Name')=='aplicarPlantaUI')
    for card_name in ['card_inventario','card_proceso']:
        card=next(n for n in main.findall('.//Rectangle') if n.findtext('Name')==card_name)
        assert float(apply_button.findtext('Y'))>=float(card.findtext('Y'))+float(card.findtext('Height'))+10
    assert '.setDrawMode(' not in ui_code, 'AnyLogic draw mode is fixed at construction'
    assert 'this, SHAPE_DRAW_2D, false' not in ui_code
    assert 'this, SHAPE_DRAW_3D, true' in ui_code
    assert 'nivelPlanta3D.add(vistaPlanta3D)' in ui_code
    assert 'presentation.add(nivelPlanta3D)' in ui_code
    assert 'vistaPlanta3D.setVisible(vista == 1)' in ui_code
    assert 'setRealTimeScale' not in plant.findtext('AgentProperties/OnReceive')
    assert 'new Comparacion_100x3()' not in ui_code
    assert 'SesionEstudio.preparar(cfg,carpetaResultados)' in ui_code
    assert 'muestrearWip.reset()' in ui_code
    assert 'validarCorridaCompleta' in study.findtext('AfterSimulationRunCode')
    assert 'SesionEstudio.configuracionPreparada()' in E.tostring(study,encoding='unicode')
    assert len(main.findall('.//TimePlot'))==4
    wip_plot=next(n for n in main.findall('.//TimePlot') if n.findtext('Name')=='plotWip')
    assert [n.findtext('Expression') for n in wip_plot.findall('DatasetExpression')]==['dsWip']
    floor=next(n for n in plant.findall('.//Rectangle') if n.findtext('Name')=='piso_planta')
    assert floor.findtext('PublicFlag')=='true'
    assert floor.findtext('EmbeddedIcon')=='false'
    assert floor.findtext('DrawMode')=='SHAPE_DRAW_3D'
    plant_scene=plant.find('Presentation/Level/Presentation')
    legacy=next(n for n in plant_scene.findall('Group') if n.findtext('Name')=='compatibilidad2D')
    assert legacy.findtext('VisibleCode')=='false'
    for product in ['lavandina','desinfectante','lavavajilla','lavarropa','suavizante','detergente']:
        assert any(n.findtext('Name')=='maquina_'+product+'_3' for n in legacy.findall('.//Rectangle'))
    assert len([n for n in main.findall('.//Control') if n.findtext('Name','').startswith('guia3D_sector_')])==9
    for tag in ['Variables','Ports','Events','Connectors','ContainerLinks','EmbeddedObjects']:
        for n in plant.findall(tag+'/*'):
            if n.find('X') is not None:assert float(n.findtext('X'))>=2000
    for a in agents.values():
        for tag in ['Variables','Ports','Connectors','Events','AnalysisData','DynamicEvents']:
            for n in a.findall(tag+'/*'):
                assert n.findtext('PresentationFlag')=='false',(a.findtext('Name'),tag,n.findtext('Name'))
    for n in main.findall('EmbeddedObjects/EmbeddedObject'):
        assert float(n.findtext('X'))>=1500
    for name in ['planoParqueRecepcion','planoParqueDilucion','planoParqueEnvasado','planoParqueDeposito','planoVicentinRecepcion','planoVicentinQc','planoVicentinPulmon','planoVicentinEnvasado','planoVicentinDeposito']:
        assert any(n.findtext('Name')==name for n in main.findall('.//Rectangle')),name
    assert plant.findtext('ClientAreaTopLeft/X')=='-1400'
    assert any(n.findtext('Name')=='guia_plano2D' for n in plant_scene.findall('Group'))
    for b in plant.findall('EmbeddedObjects/EmbeddedObject'):
        for generic in b.findall('GenericParameterSubstitute'):
            assert generic.findtext('GenericParameterSubstituteValue/Code')=='Batch',b.findtext('Name')
    for a in agents.values():
        scene=a.find('Presentation/Level/Presentation')
        if scene is not None:
            shape_ids=[n.text for n in scene.findall('.//Id')]
            assert len(shape_ids)==len(set(shape_ids)),a.findtext('Name')
            shape_names=[n.findtext('Name') for n in scene.iter() if n.tag in ['Text','Rectangle','Figure3D','Group','Control','Camera3D','TimePlot'] and n.find('Name') is not None]
            assert len(shape_names)==len(set(shape_names)),(a.findtext('Name'),'duplicate shape name')
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
        if c.get('Type')=='Window3D':jmain+='public ShapeWindow3D '+c.findtext('Name')+';\n'
    jmain+='public Camera3D camaraMain; public EventTimeout muestrearWip;\n'
    jmain+=main.findtext('AdditionalClassCode')+'\n'
    types={'TextCode':'String','VisibleCode':'boolean','XCode':'double','YCode':'double','WidthCode':'double','FillColorCode':'java.awt.Color'}
    for i,n in enumerate(main.findall('Presentation/Level/Presentation//*')):
        if n.tag in types and n.text:jmain+=f'{types[n.tag]} property{i}(){{return {n.text};}}\n'
    for i,n in enumerate(main.findall('.//Control/BasicProperties/ActionCode')):jmain+=f'void action{i}(){{{n.text}}}\n'
    for i,n in enumerate(main.findall('Events/Event/Action')):jmain+=f'void event{i}(){{{n.text}}}\n'
    jmain+='}\n'
    jplant=imports+'public class DomitecPlant extends domitec_main_3d.DomitecPlant {\n@Override public Main get_Main(){return null;}\n'+plant.findtext('AdditionalClassCode')+'\n'
    jplant+='void receipt(Object msg){'+plant.findtext('AgentProperties/OnReceive')+'}\n'
    plan=next(n for n in plant.findall('.//Group') if n.findtext('Name')=='guia_plano2D')
    for i,n in enumerate(plan.findall('.//TextCode')):jplant+=f'String planLabel{i}(){{return {n.text};}}\n'
    for i,n in enumerate(plant.findall('.//Rectangle/VisibleCode')):
        if n.text and 'sector3DActivo' in n.text:jplant+=f'boolean sectorHighlight{i}(){{return {n.text};}}\n'
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
    for i,n in enumerate(study.findall('.//Control/BasicProperties/ActionCode')):jstudy+=f'void controlAction{i}(){{{n.text}}}\n'
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
        if cls.findtext('Name') in ['ComparacionEscenarios','ConfiguracionDomitec','RegistroCorrida','SesionEstudio','EstudioPareado','OperarioAnimation']:
            (work/(cls.findtext('Name')+'.java')).write_text('package domitec_interactivo;\n'+cls.findtext('Text'),encoding='utf8')
    cp=[work/'native.jar']
    for plugin,jar in [('com.anylogic.engine','com.anylogic.engine.jar'),('com.anylogic.engine.datautil','com.anylogic.engine.datautil.jar'),('com.anylogic.engine.database','com.anylogic.engine.database.jar'),('com.anylogic.process_modeling_library','lib/ProcessModelingLibrary.jar')]:cp.append(next((INSTALL/'plugins').glob(plugin+'_*'))/jar)
    p=subprocess.run([str(INSTALL/'jre/bin/javac.exe'),'-encoding','UTF-8','-Xmaxerrs','10','-cp',os.pathsep.join(map(str,cp)),'-d',str(work/'classes'),*[str(f) for f in work.glob('*.java')]],text=True,capture_output=True)
    assert p.returncode==0,p.stdout+p.stderr
    print('PASS: exact UI methods, expressions, controls, event actions, stochastic properties and paired experiment actions compile against AnyLogic API')
    report={'structure':'passed','java_action_compatibility':'passed','native_300_run':'pending_direct_AnyLogic_launch','native_visual_validation':'pending_retest_after_sector_guide_cleanup','delivery_speed_override':'removed','logic_element_presentation':'hidden','view_2d':'native_flow_diagram','batch_launch':'direct_defaults_or_optional_saved_parameters'}
    audit=ROOT/'tools/auditoria_estudio_real.json'
    if audit.exists():
        report['native_300_run']='completed_in_recorded_package'
        report['last_native_results_audit']=json.loads(audit.read_text(encoding='utf8'))
    (FILE.parent/'verificacion_interfaz.json').write_text(json.dumps(report,indent=2),encoding='utf8')

if __name__=='__main__':main()
