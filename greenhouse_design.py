"""Transparent preliminary greenhouse sizing. Not an EnergyPlus simulation.

Cooling is sensible peak-load screening; ventilation uses an assumed allowable
indoor/outdoor temperature rise. Irrigation is a radiation-based ET proxy, NOT
FAO-56 Penman-Monteith or a crop water-balance model.
"""
import math

# Screening ranges for daily light integral (mol PAR m-2 day-1), NOT crop
# cultivar-specific agronomic prescriptions.
CROP_LIGHT = {
    'Tomato': (20.,30.), 'Cucumber': (18.,28.), 'Pepper': (18.,26.),
    'Lettuce': (12.,17.), 'Strawberry': (15.,22.), 'Rose': (18.,25.),
    'Orchid': (8.,15.), 'Anthurium': (8.,14.), 'Chrysanthemum': (12.,20.),
    'Geranium': (12.,20.), 'Lily': (14.,22.), 'Iris': (14.,22.),
    'Carnation': (14.,22.), 'Citrus': (18.,25.), 'Carrot': (12.,20.),
    'Potato': (14.,22.), 'Onion': (15.,22.), 'Cabbage': (12.,20.),
    'Broccoli': (12.,20.),
}
# Indicative crop coefficients, dimensionless; development stage dependent.
CROP_KC = {'Tomato':1.10,'Cucumber':1.0,'Pepper':1.05,'Lettuce':1.0,
           'Strawberry':0.85,'Rose':1.0,'Orchid':0.8,'Anthurium':0.8,
           'Chrysanthemum':1.0,'Geranium':0.9,'Lily':1.0,'Iris':1.0,
           'Carnation':1.0,'Citrus':0.75,'Carrot':1.05,'Potato':1.1,
           'Onion':1.0,'Cabbage':1.05,'Broccoli':1.05}

def design_greenhouse(*,geometry, crop, u_value, ach, heating_setpoint,
                      heating_outdoor, cooling_setpoint, cooling_outdoor,
                      solar_irradiance_wm2, glazing_transmittance,
                      shading_fraction, crop_coverage, ventilation_delta_t,
                      max_air_changes, air_density=1.2, cp_air=1005.,
                      irrigation_et0_mm_day=4., irrigation_efficiency=0.85,
                      leaching_fraction=0.10, par_dli_outdoor=25.,
                      lamp_efficacy=2.5, photoperiod_h=14.,
                      roof_vent_capacity_m3h=0.):
    floor=geometry['floor_area_m2']
    volume=geometry['volume_m3']
    envelope=geometry['envelope_m2']
    roof=geometry['roof_area_m2']
    if floor<=0 or volume<=0: raise ValueError('Greenhouse dimensions must be positive.')
    if not 0<irrigation_efficiency<=1 or not 0<=leaching_fraction<1:
        raise ValueError('Invalid irrigation efficiency or leaching fraction.')
    if not 0<lamp_efficacy or photoperiod_h<=0 or ventilation_delta_t<=0:
        raise ValueError('Invalid lighting or ventilation inputs.')
    heating=geometry['heating_kw']
    # Sensible cooling: solar transmitted + conduction/infiltration heat gains.
    # Conservative simplification: no canopy latent heat, thermal mass, ground
    # heat, solar angle, or active shading controls.
    solar_gain_kw=solar_irradiance_wm2*roof*glazing_transmittance*(1-shading_fraction)/1000
    dt=max(0.,cooling_outdoor-cooling_setpoint)
    conduction_kw=u_value*envelope*dt/1000
    infiltration_kw=air_density*cp_air*(ach*volume/3600)*dt/1000
    cooling_kw=solar_gain_kw+conduction_kw+infiltration_kw
    # Ventilation required to remove solar gain if intake is sufficiently cool.
    # If outdoor air is warmer than indoor setpoint, ventilation cannot meet
    # cooling setpoint alone, and mechanical/evaporative cooling is required.
    outdoor_suitable=cooling_outdoor<cooling_setpoint
    effective_dt=min(ventilation_delta_t,max(0.,cooling_setpoint-cooling_outdoor))
    airflow_required=(solar_gain_kw*1000*3600/(air_density*cp_air*effective_dt)
                      if effective_dt>0 else None)
    airchanges_required=(airflow_required/volume if airflow_required is not None else None)
    installed_ventilation=max_air_changes*volume
    available_ventilation=roof_vent_capacity_m3h if roof_vent_capacity_m3h>0 else installed_ventilation
    kc=CROP_KC.get(crop,1.)
    net_irrigation_m3d=irrigation_et0_mm_day*kc*floor*crop_coverage/1000
    gross_irrigation_m3d=net_irrigation_m3d/(irrigation_efficiency*(1-leaching_fraction))
    target_dli=CROP_LIGHT.get(crop,(15.,22.))
    natural_dli=par_dli_outdoor*glazing_transmittance*(1-shading_fraction)
    missing_dli=max(0.,target_dli[0]-natural_dli)
    # 1 mol PAR = 1e6 umol. Lamp efficacy umol/J -> kWh.
    lamp_kwh_m2_day=missing_dli*1e6/lamp_efficacy/3.6e6
    lamp_energy_kwh_day=lamp_kwh_m2_day*floor*crop_coverage
    lamp_power_kw=lamp_energy_kwh_day/photoperiod_h
    return {
        'floor_area_m2':floor,'roof_area_m2':roof,'envelope_m2':envelope,'volume_m3':volume,
        'heating_kw':heating,'solar_gain_kw':solar_gain_kw,
        'cooling_conduction_kw':conduction_kw,'cooling_infiltration_kw':infiltration_kw,
        'cooling_sensible_kw':cooling_kw,
        'ventilation_required_m3h':airflow_required,
        'ventilation_required_ach':airchanges_required,
        'ventilation_available_m3h':available_ventilation,
        'ventilation_sufficient':(airflow_required is not None and available_ventilation>=airflow_required),
        'outdoor_air_cooling_possible':outdoor_suitable,
        'net_irrigation_m3_day':net_irrigation_m3d,
        'gross_irrigation_m3_day':gross_irrigation_m3d,
        'crop_coefficient_assumed':kc,
        'dli_target_min_mol_m2_day':target_dli[0],
        'dli_target_max_mol_m2_day':target_dli[1],
        'natural_dli_mol_m2_day':natural_dli,
        'supplemental_dli_mol_m2_day':missing_dli,
        'supplemental_lighting_kw':lamp_power_kw,
        'supplemental_lighting_kwh_day':lamp_energy_kwh_day,
    }
