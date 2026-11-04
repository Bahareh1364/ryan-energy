'''Generate and execute a WaterTAP seawater RO 0D flowsheet from RYAN design inputs.
Requires compatible WaterTAP, IDAES, Pyomo, and an available nonlinear solver.
No fallback or fake WaterTAP result is returned if solve fails.
'''
import json,subprocess,sys,tempfile
from pathlib import Path

def build_ro_script(inputs):
    vals=json.dumps(inputs)
    return '''import json
from pyomo.environ import ConcreteModel, value, units as pyunits, check_optimal_termination
from idaes.core import FlowsheetBlock
from idaes.core.solvers import get_solver
from watertap.property_models.seawater_prop_pack import SeawaterParameterBlock
from watertap.unit_models.reverse_osmosis_0D import ReverseOsmosis0D
from watertap.core import ConcentrationPolarizationType, MassTransferCoefficient, PressureChangeType
from watertap.core.util.initialization import interval_initializer

p=json.loads('''+repr(vals)+''')
m=ConcreteModel()
m.fs=FlowsheetBlock(dynamic=False)
m.fs.properties=SeawaterParameterBlock()
m.fs.ro=ReverseOsmosis0D(property_package=m.fs.properties,
    has_pressure_change=False,
    concentration_polarization_type=ConcentrationPolarizationType.none,
    mass_transfer_coefficient=MassTransferCoefficient.none)
ro=m.fs.ro
rho=1025.0
feed_m3_s=p['product_m3_day']/86400.0/p['recovery']
feed_kg_s=feed_m3_s*rho
salt_frac=p['tds_mg_l']/1e6
ro.inlet.flow_mass_phase_comp[0,'Liq','H2O'].fix(feed_kg_s*(1-salt_frac))
ro.inlet.flow_mass_phase_comp[0,'Liq','TDS'].fix(feed_kg_s*salt_frac)
ro.inlet.temperature[0].fix(p['temperature_c']+273.15)
ro.inlet.pressure[0].fix(p['pressure_bar']*1e5)
ro.area.fix(p['membrane_area_m2'])
ro.A_comp.fix(p['water_permeability_m_pa_s'])
ro.B_comp.fix(p['salt_permeability_m_s'])
# An RO model needs feed-side and permeate-side pressure boundary conditions.
ro.permeate.pressure[0].fix(101325)
solver=get_solver()
ro.initialize()
results=solver.solve(m,tee=False)
if not check_optimal_termination(results):
    raise RuntimeError('WaterTAP solver did not reach optimal termination: '+str(results.solver.termination_condition))
perm_kg_s=value(ro.mixed_permeate[0].flow_mass_phase_comp['Liq','H2O'])+value(ro.mixed_permeate[0].flow_mass_phase_comp['Liq','TDS'])
perm_m3_day=perm_kg_s/rho*86400
brine_kg_s=value(ro.retentate.flow_mass_phase_comp[0,'Liq','H2O'])+value(ro.retentate.flow_mass_phase_comp[0,'Liq','TDS'])
print('RYAN_WATERTAP_RESULT='+json.dumps({'water_m3_day':perm_m3_day,'brine_m3_day':brine_kg_s/rho*86400,
 'feed_m3_day':feed_m3_s*86400,'recovery_calculated':perm_kg_s/feed_kg_s,
 'membrane_area_m2':value(ro.area),'solver_status':str(results.solver.termination_condition)}))
'''

def run_ro(inputs,timeout=240):
    with tempfile.TemporaryDirectory(prefix='ryan_ro_') as td:
        script=Path(td)/'ro.py';script.write_text(build_ro_script(inputs),encoding='utf-8')
        proc=subprocess.run([sys.executable,str(script)],cwd=td,capture_output=True,text=True,timeout=timeout)
        if proc.returncode:
            raise RuntimeError('Native WaterTAP run failed; no result has been substituted.\n'+(proc.stderr or proc.stdout)[-4500:])
        for line in proc.stdout.splitlines():
            if line.startswith('RYAN_WATERTAP_RESULT='):
                return json.loads(line.partition('=')[2])
        raise RuntimeError('WaterTAP did not return the expected results.\n'+proc.stdout[-2000:])
