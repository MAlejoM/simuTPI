"""Compile AnyLogic's actual generated sources, without launching its runtime.

This checks code generation, unlike the separate action compatibility harness.
It never changes the generated project or the running editor.
"""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, xml.etree.ElementTree as E
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path.home()/'.AnyLogicPLE/Workspace8.8/Domitec_Interactivo_BUILD'
WORK = ROOT/'tools/_workspace_java_generado'
INSTALL = Path(r'D:\AnyLogic 8.9 Personal Learning Edition')

def main():
    source = BUILD/'src.generated'
    assert source.is_dir(), source
    native_plant=(source/'domitec_interactivo/DomitecPlant.java').read_text(encoding='utf8')
    assert 'finalizarLote' in native_plant and 'BalanceMateriales' in native_plant, \
        'AnyLogic must regenerate the corrected 24x7 operating model before compilation'
    native_config=(source/'domitec_interactivo/ConfiguracionDomitec.java').read_text(encoding='utf8')
    assert 'operacion-24x7-v2' in native_config, 'Stale native configuration: reload the updated ALP in AnyLogic'
    assert re.search(r'piso_planta\s*=\s*new ShapeRectangle\(\s*SHAPE_DRAW_3D,\s*true',native_plant), \
        'AnyLogic must regenerate the floor as a public 3D shape, not a 2D icon'
    icon_line=next(line for line in native_plant.splitlines() if 'icon = new ShapeModelElementsGroup' in line)
    assert 'piso_planta' not in icon_line, 'The floor must belong to the scene, not the model icon'
    assert re.search(r'_origin_VA\s*=\s*new ViewArea\(\s*this,\s*"\[Origin\]",\s*-1400(?:\.0)?,',native_plant), \
        'AnyLogic must regenerate DomitecPlant origin at the restored 2D plan'
    target = WORK/'src'
    target.mkdir(parents=True, exist_ok=True)
    files = []
    for original in source.rglob('*.java'):
        copied = target/original.relative_to(source)
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, copied)
        files.append(copied)
    cp = [e.get('path') for e in E.parse(BUILD/'.classpath').findall('classpathentry')
          if e.get('kind') == 'lib']
    args = ['-encoding','UTF-8','-Xmaxerrs','40','-cp',os.pathsep.join(cp),
            '-d',str(WORK/'classes'),*[str(f) for f in files]]
    argfile = WORK/'javac.args'
    argfile.write_text('\n'.join('"'+a.replace('\\','/')+'"' for a in args), encoding='utf8')
    result = subprocess.run([str(INSTALL/'jre/bin/javac.exe'),'@'+str(argfile)],
                            text=True,capture_output=True)
    (WORK/'compilacion.txt').write_text(result.stdout+result.stderr,encoding='utf8')
    print(result.stdout+result.stderr)
    print(f'AnyLogic generated sources: {len(files)}; javac exit={result.returncode}')
    report = ROOT/'domitec_interactivo/verificacion_interfaz.json'
    data = json.loads(report.read_text(encoding='utf8')) if report.exists() else {}
    data['native_generated_java'] = {
        'status': 'passed' if result.returncode == 0 else 'failed',
        'file_count': len(files), 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256': hashlib.sha256(b''.join(f.read_bytes() for f in sorted(files))).hexdigest(),
        'note': 'Compilation only; does not certify simulation completion or statistical results.'
    }
    report.write_text(json.dumps(data,indent=2),encoding='utf8')
    raise SystemExit(result.returncode)

if __name__ == '__main__': main()
