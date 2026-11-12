"""Validate the delivered operating model and run material/order/calendar tests.

This does not claim to execute AnyLogic or validate the plant statistically.
"""
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as E
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
JAVA=next(p/'jre/bin' for p in [Path(r'C:\Program Files\AnyLogic 8.9 Personal Learning Edition'), Path(r'D:\AnyLogic 8.9 Personal Learning Edition')] if (p/'jre/bin/javac.exe').is_file())

def main():
    path=ROOT/'domitec_interactivo/Domitec_Interactivo.alp'
    model=E.parse(path).getroot().find('Model')
    agents={a.findtext('Name'):a for a in model.findall('ActiveObjectClasses/ActiveObjectClass')}
    plant=agents['DomitecPlant'];main=agents['Main']
    classes={c.findtext('Name'):c.findtext('Text') for c in model.findall('JavaClasses/JavaClass')}
    for name in ['CalendarioPlanta','BalanceMateriales','DatosOperativos','ConfiguracionDomitec',
                 'RegistroCorrida','ComparacionEscenarios','SesionEstudio','EstudioPareado']:
        assert classes[name]==(ROOT/'tools'/f'{name}.java').read_text(encoding='utf8'),name
    assert 'public double horas = 168.0;' in classes['ConfiguracionDomitec']
    assert 'operacion-24x7-v2' in classes['ConfiguracionDomitec']
    event=next(n for n in plant.findall('Events/Event') if n.findtext('Name')=='avanceProduccion')
    assert event.findtext('ExcludeFromBuild') in (None, 'false') and event.findtext('Action')=='operarPlanta();'
    assert 'sourceLavandina.inject' not in plant.findtext('AgentProperties/OnReceive')
    assert 'materiales.recibir' in plant.findtext('AgentProperties/OnReceive')
    assert 'productionLines' not in plant.findtext('StartupCode')
    for b in plant.findall('EmbeddedObjects/EmbeddedObject'):
        name=b.findtext('Name');p={n.findtext('Name'):n for n in b.findall('Parameters/Parameter')}
        if name.startswith(('delay','queue','tank')):
            assert p['maximumCapacity'].findtext('Value/Code')=='false',name
            assert p['capacity'].findtext('Value/Code'),name
        if name.startswith('delay'):assert p['delayTime'].findtext('Value/Unit')=='WEEK',name
        if name.startswith('sink'):
            body=p['onEnter'].findtext('Value/Code','');assert body.count('finalizarLote(agent,')==1,name
    assert 'materiales.materiaPrima(p)+materiales.enProceso(p)' in next(n.findtext('Action') for n in plant.findall('Events/Event') if n.findtext('Name')=='planificacionSemanal')
    assert 'return ((DomitecPlant)domitecPlant).materiales.wip();' in main.findtext('AdditionalClassCode')
    assert 'canceladasActual()' in main.findtext('AdditionalClassCode')
    print('PASS: serialized runtime, finite buffers, material release, 24x7 clock, single production flow, cancellation ledger')
    work=ROOT/'tools/_workspace_operacion_v2';work.mkdir(exist_ok=True)
    tests=['TestCalendarioPlanta','TestBalanceMateriales','TestCancelacionPedidos','TestDatosOperativos',
           'TestRegistroConfiguracion','TestComparacionEscenarios','TestPreparacionEstudio','TestEstudioPareado']
    sources=['CalendarioPlanta','BalanceMateriales','DatosOperativos','RegistroCorrida','ConfiguracionDomitec',
             'ComparacionEscenarios','EstudioPareado','SesionEstudio']+tests
    compiled=subprocess.run([str(JAVA/'javac.exe'),'-encoding','UTF-8','-d',str(work),
                              *[str(ROOT/'tools'/f'{n}.java') for n in sources]],text=True,capture_output=True)
    assert compiled.returncode==0,compiled.stderr
    for name in tests:
        p=subprocess.run([str(JAVA/'java.exe'),'-cp',str(work),name],capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=work)
        assert p.returncode==0,name+'\n'+p.stdout+p.stderr
        print(p.stdout.strip())
    audit_path=ROOT/'tools/auditoria_estudio_real.json'
    if audit_path.exists():
        audit=json.loads(audit_path.read_text(encoding='utf8'))
        for name,expected in audit['hashes_sha256'].items():
            assert hashlib.sha256((ROOT/audit['package']/name).read_bytes()).hexdigest()==expected,name
        print('PASS: previous 100x3 results preserved byte for byte')
    report={'model_version':'operacion-24x7-v2','model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'checked_utc':datetime.now(timezone.utc).isoformat(),'structure':'passed','java_tests':tests,
            'native_simulation':'pending_AnyLogic_run','statistical_calibration':'provisional',
            'unidentified_inputs':['customer_patience_days','physical_WIP_release_limit','production_year','intramonth_demand_variability']}
    (ROOT/'domitec_interactivo/verificacion_operacion.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
