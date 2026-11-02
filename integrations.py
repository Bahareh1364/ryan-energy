"""Optional adapters for installed external engines; never silently substitute estimates."""
from pathlib import Path
import importlib.util
import shutil
import subprocess
import tempfile
import json
import sys


def engine_status(energyplus_path=''):
    ep=Path(energyplus_path) if energyplus_path else None
    ep_exec=str(ep) if ep and ep.is_file() else shutil.which('energyplus')
    return {
        'pvlib': bool(importlib.util.find_spec('pvlib')),
        'PyPSA': bool(importlib.util.find_spec('pypsa')),
        'EnergyPlus': bool(ep_exec),
        'WaterTAP': bool(importlib.util.find_spec('watertap')),
        'EnergyPlus executable': ep_exec or '',
    }


def run_energyplus(idf_bytes, epw_bytes, executable, timeout=300):
    """Run user's complete IDF + EPW through installed EnergyPlus.
    This does not turn a greenhouse geometry into an IDF automatically.
    """
    if not executable or not Path(executable).is_file():
        raise FileNotFoundError('Provide the full path to energyplus.exe')
    if not idf_bytes or not epw_bytes:
        raise ValueError('Both an EnergyPlus IDF and an EPW weather file are required.')
    with tempfile.TemporaryDirectory(prefix='ryan_ep_') as tmp:
        folder=Path(tmp)
        (folder/'model.idf').write_bytes(idf_bytes)
        (folder/'weather.epw').write_bytes(epw_bytes)
        proc=subprocess.run([str(executable),'-w',str(folder/'weather.epw'),'-d',str(folder/'out'),str(folder/'model.idf')],
                            capture_output=True,text=True,timeout=timeout)
        err=(folder/'out'/'eplusout.err')
        report=err.read_text(errors='replace')[-10000:] if err.exists() else proc.stderr[-10000:]
        if proc.returncode:raise RuntimeError(f'EnergyPlus failed (code {proc.returncode}):\n{report}')
        csv=folder/'out'/'eplusout.csv'
        return {'log':report,'csv_bytes':csv.read_bytes() if csv.exists() else None,
                'status':'Completed; inspect severe/fatal warnings and model suitability.'}


def watertap_diagnostic():
    """Import diagnostic only; a working flowsheet is NOT implied."""
    try:
        import watertap
        from importlib.metadata import version
        return {'installed':True,'version':version('watertap'),
                'message':'Installed. A process-specific flowsheet and compatible solver are still required.'}
    except Exception as exc:
        return {'installed':False,'message':str(exc)}


def run_watertap_script(script_bytes, timeout=300):
    """Run a supplied WaterTAP Python flowsheet in a separate process.
    Only execute trusted scripts; Python scripts have full local access.
    """
    if not watertap_diagnostic()['installed']:
        raise RuntimeError('WaterTAP is not installed in this Python environment.')
    if not script_bytes:
        raise ValueError('Supply a WaterTAP flowsheet script.')
    with tempfile.TemporaryDirectory(prefix='ryan_wt_') as tmp:
        script=Path(tmp)/'flowsheet.py';script.write_bytes(script_bytes)
        proc=subprocess.run([sys.executable,str(script)],cwd=tmp,capture_output=True,text=True,timeout=timeout)
        if proc.returncode:raise RuntimeError('WaterTAP script failed:\n'+proc.stderr[-10000:])
        return proc.stdout[-30000:]
