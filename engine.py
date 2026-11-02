"""Independent engineering core. No Streamlit dependencies."""
import numpy as np
import pandas as pd

def pv_profile(df, lat, lon, tilt, azimuth, module_w, n_modules, gamma=-0.0035, losses=0.14, inverter_eff=0.96):
    import pvlib
    times = pd.DatetimeIndex(pd.to_datetime(df['time'], utc=True))
    loc = pvlib.location.Location(lat, lon, tz='UTC')
    sun = loc.get_solarposition(times)
    poa = pvlib.irradiance.get_total_irradiance(tilt,azimuth,sun['apparent_zenith'].to_numpy(),sun['azimuth'].to_numpy(),
            dni=np.maximum(df['dni'].to_numpy(float),0),ghi=np.maximum(df['ghi'].to_numpy(float),0),dhi=np.maximum(df['dhi'].to_numpy(float),0),model='isotropic')['poa_global']
    temp = df['temp_air'].to_numpy(float)
    ws = np.maximum(df['wind_ms'].to_numpy(float),0.1)
    cell = pvlib.temperature.faiman(poa,temp,ws)
    dc_kw = module_w*n_modules/1000*np.maximum(poa,0)/1000*np.maximum(0,1+gamma*(cell-25))
    ac_kw = np.maximum(0,dc_kw*(1-losses)*inverter_eff)
    return pd.Series(ac_kw,index=times,name='Solar PV (kW)')

def wind_profile(df, rated_kw, n_turbines, hub_m, cutin, rated_ms, cutout, alpha=0.14, losses=0.16, power_curve=None):
    v=np.maximum(df['wind_ms'].to_numpy(float),0)*(hub_m/10)**alpha
    if power_curve is not None:
        curve=power_curve.sort_values('wind_ms')
        fraction=np.interp(v,curve['wind_ms'],curve['power_kw'],left=0,right=0)/rated_kw
        fraction=np.where((v<cutin)|(v>=cutout),0,fraction)
    else:
        if not (0<cutin<rated_ms<cutout): raise ValueError('Wind cut-in < rated < cut-out is required.')
        fraction=np.where((v<cutin)|(v>=cutout),0,np.where(v>=rated_ms,1,(v**3-cutin**3)/(rated_ms**3-cutin**3)))
    times=pd.DatetimeIndex(pd.to_datetime(df['time'],utc=True))
    return pd.Series(rated_kw*n_turbines*np.clip(fraction,0,1)*(1-losses),index=times,name='Wind (kW)')

def design_count(mode, budget, land, count, unit_price, fixed_cost, unit_land):
    if mode=='Budget-Based': return max(0,int((budget-fixed_cost)//unit_price)) if unit_price>0 else 0
    if mode=='Land-Based': return max(0,int(land//unit_land)) if unit_land>0 else 0
    return max(0,int(count))

def economic_metrics(annual_kwh, capex, opex_annual, tariff, lifetime, discount, degradation=0):
    years=np.arange(1,lifetime+1)
    energies=annual_kwh*(1-degradation)**(years-1)
    revenues=energies*tariff
    flows=revenues-opex_annual
    npv=-capex+np.sum(flows/(1+discount)**years)
    lcoe=(capex+np.sum(opex_annual/(1+discount)**years))/max(1e-9,np.sum(energies/(1+discount)**years))
    cumulative=np.cumsum(flows)-capex
    payback=int(np.where(cumulative>=0)[0][0]+1) if (cumulative>=0).any() else None
    return {'CAPEX':capex,'Annual OPEX':opex_annual,'NPV':npv,'LCOE':lcoe,'Simple payback (years)':payback}

def pypsa_dispatch(df, pv, wind, demand_kw, grid_cost, battery_kwh, battery_kw, battery_eff=0.9):
    """Hourly least-cost dispatch, fixed generation assets, optional battery, unlimited grid backup.
    Returns PyPSA optimization results and timeseries; energy balance is physically enforced.
    """
    import pypsa
    if not (0<battery_eff<=1):raise ValueError('Battery efficiency must be in (0,1].')
    times=pd.DatetimeIndex(pd.to_datetime(df['time'],utc=True)).tz_localize(None)
    if len(times)!=len(pv) or len(times)!=len(wind):raise ValueError('Profile lengths differ.')
    n=pypsa.Network();n.set_snapshots(times)
    n.add('Bus','electricity')
    n.add('Load','demand',bus='electricity',p_set=float(demand_kw))
    for name,profile in [('Solar',pv),('Wind',wind)]:
        rated=max(float(profile.max()),0.0001)
        n.add('Generator',name,bus='electricity',p_nom=rated,p_max_pu=np.clip(profile.to_numpy()/rated,0,1),marginal_cost=0)
    # A zero-cost system has an identically zero objective in some PyPSA versions.
    # Give grid imports a small strictly positive optimization cost only if
    # user sets grid_cost=0. This is a tie-breaker, not an economic tariff.
    solver_grid_cost=max(float(grid_cost), 0.01)
    n.add('Generator','Grid',bus='electricity',p_nom=max(float(demand_kw)*2,1),marginal_cost=solver_grid_cost)
    if battery_kwh>0 and battery_kw>0:
        n.add('StorageUnit','Battery',bus='electricity',p_nom=float(battery_kw),max_hours=float(battery_kwh)/float(battery_kw),
              efficiency_store=float(battery_eff)**0.5,efficiency_dispatch=float(battery_eff)**0.5,
              cyclic_state_of_charge=True,marginal_cost=0.001)
    # Ensure the objective exists even when all installed capacities are fixed,
    # generation costs are zero and no storage is configured.
    status,condition=n.optimize(solver_name='highs',log_to_console=False)
    if status!='ok':raise RuntimeError(f'PyPSA solver: {status}, {condition}')
    out=pd.DataFrame(index=times)
    out['Demand (kW)']=float(demand_kw)
    for name in ('Solar','Wind','Grid'):out[name+' (kW)']=n.generators_t.p[name].to_numpy()
    if 'Battery' in n.storage_units.index:
        out['Battery dispatch (kW)']=n.storage_units_t.p['Battery'].to_numpy()
        out['Battery SOC (kWh)']=n.storage_units_t.state_of_charge['Battery'].to_numpy()
    out['Curtailment (kW)']=np.maximum(0,pv.to_numpy()+wind.to_numpy()-out['Solar (kW)'].to_numpy()-out['Wind (kW)'].to_numpy())
    return out

def desalination(daily_m3,sec_kwh_m3):return daily_m3*sec_kwh_m3
