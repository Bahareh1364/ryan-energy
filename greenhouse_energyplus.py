'''Automatically generate an EnergyPlus equivalent single-zone greenhouse thermal model.
This is a thermal approximation, not curved-geometry, plant-transpiration or structural simulation.
'''
from pathlib import Path
import math

def generate_greenhouse_idf(design, heating_setpoint_c=18., cooling_setpoint_c=32.,
                            glazing_u=5.8, ach=1., name='RYAN Greenhouse'):
    area=float(design['floor_area_m2']); volume=float(design['volume_m3'])
    if area<=0 or volume<=0:raise ValueError('Greenhouse area and volume must be positive.')
    # Equivalent rectangular thermal zone preserves floor area and reference volume.
    width=math.sqrt(area/2.0); length=area/width; height=volume/area
    if not (0.2<height<100):raise ValueError('Equivalent greenhouse height out of bounds.')
    # Equivalent roof and walls are not an exact curved A/B/C representation.
    def surface(n,typ,construction,bc,sun,wind,vertices):
        coords=',\n'.join(f'  {x:.5f}, {y:.5f}, {z:.5f}' for x,y,z in vertices)
        return f'''BuildingSurface:Detailed,
  {n}, {typ}, {construction}, GH Zone, {bc}, , {sun}, {wind}, 0.5,
  {len(vertices)},
{coords};
'''
    # Surface vertex winding consistent with outward-facing normals.
    surfaces=[
      surface('Floor','Floor','Ground Slab','Ground','NoSun','NoWind',[(0,0,0),(0,length,0),(width,length,0),(width,0,0)]),
      surface('Roof','Roof','GH Cover','Outdoors','SunExposed','WindExposed',[(0,0,height),(width,0,height),(width,length,height),(0,length,height)]),
      surface('West','Wall','GH Cover','Outdoors','SunExposed','WindExposed',[(0,length,0),(0,0,0),(0,0,height),(0,length,height)]),
      surface('East','Wall','GH Cover','Outdoors','SunExposed','WindExposed',[(width,0,0),(width,length,0),(width,length,height),(width,0,height)]),
      surface('South','Wall','GH Cover','Outdoors','SunExposed','WindExposed',[(0,0,0),(width,0,0),(width,0,height),(0,0,height)]),
      surface('North','Wall','GH Cover','Outdoors','SunExposed','WindExposed',[(width,length,0),(0,length,0),(0,length,height),(width,length,height)]),
    ]
    # Opaque equivalent covering: matches specified U but not solar transmission.
    # A separate transparent glazing model is required for validated greenhouse loads.
    r=max(0.01,1/glazing_u-0.17)
    idf=f'''Version, 9.6;
Building, RYAN Greenhouse, 0, Suburbs, 0.04, 0.4, FullExterior, 25, 6;
Timestep, 4;
SimulationControl, No, No, No, Yes, Yes;
RunPeriod, Annual, 1, 1, , 12, 31;
Site:GroundTemperature:BuildingSurface, 18,18,18,18,18,18,18,18,18,18,18,18;
ScheduleTypeLimits, Any Number;
Schedule:Constant, Always On, Any Number, 1;
Schedule:Constant, Heating Setpoint, Any Number, {heating_setpoint_c};
Schedule:Constant, Cooling Setpoint, Any Number, {cooling_setpoint_c};
Zone, GH Zone, 0, 0, 0, 0, 1, 1, , {volume:.4f}, {area:.4f};
Material:NoMass, GH Equivalent Material, Rough, {r:.6f}, 0.5, 0.5, 0.5;
Construction, GH Cover, GH Equivalent Material;
Material, Slab Material, Rough, 0.15, 1.4, 2200, 880;
Construction, Ground Slab, Slab Material;
''' + '\n'.join(surfaces) + f'''
ZoneInfiltration:DesignFlowRate, GH Infiltration, GH Zone, Always On, AirChanges/Hour, , , , {ach}, 1, 0, 0, 0;
ThermostatSetpoint:DualSetpoint, GH Dual Setpoint, Heating Setpoint, Cooling Setpoint;
ZoneControl:Thermostat, GH Thermostat, GH Zone, Always On, ThermostatSetpoint:DualSetpoint, GH Dual Setpoint;
ZoneHVAC:IdealLoadsAirSystem, GH Ideal Loads, Always On;
ZoneHVAC:EquipmentList, GH Equipment List, SequentialLoad, ZoneHVAC:IdealLoadsAirSystem, GH Ideal Loads, 1, 1;
ZoneHVAC:EquipmentConnections, GH Zone, GH Equipment List, GH Inlet Node, , GH Air Node, GH Return Node;
Output:Variable,*,Zone Ideal Loads Supply Air Total Heating Energy,Hourly;
Output:Variable,*,Zone Ideal Loads Supply Air Total Cooling Energy,Hourly;
Output:Variable,*,Zone Mean Air Temperature,Hourly;
Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;
Output:Table:SummaryReports, AllSummary;
OutputControl:Files, Yes, Yes, Yes, Yes, Yes, Yes, Yes, Yes, Yes, Yes, Yes, Yes;
'''
    return idf.encode('utf-8'),{'floor_area_m2':area,'equivalent_width_m':width,'equivalent_length_m':length,
      'equivalent_height_m':height,'equivalent_volume_m3':volume,
      'geometry_note':'Equivalent single-zone box, not literal curved greenhouse A/B/C; opaque equivalent envelope. Plant latent heat and solar glazing omitted.'}
