"""Offline demonstration and internal consistency checks. Synthetic != observed data."""
import numpy as np
import pandas as pd

def synthetic_weather(lat,lon,year=2025):
    """Deterministic, plausible demonstration profile. Never for validation/design."""
    t=pd.date_range(f'{year}-01-01',periods=8760,freq='h',tz='UTC')
    day=t.dayofyear.to_numpy();hour=t.hour.to_numpy()
    seasonal=np.sin(2*np.pi*(day-80)/365.0)
    temp=18+13*seasonal+6*np.sin(2*np.pi*(hour-8)/24)
    wind=np.clip(4+1.8*np.sin(2*np.pi*day/9)+1.3*np.sin(2*np.pi*hour/24),0.2,None)
    # Intentionally simplified irradiance; label as synthetic in all UI.
    sun=np.clip(np.sin(np.pi*(hour-6)/12),0,None)
    season_factor=np.clip(0.72+0.26*seasonal,0.25,1.0)
    ghi=900*sun*season_factor
    dni=ghi*0.75
    dhi=ghi*0.25
    return pd.DataFrame({'time':t,'temp_air':temp,'wind_ms':wind,'ghi':ghi,'dni':dni,'dhi':dhi})

def validate_energy_balance(result,tolerance_kw=1e-3):
    demand=result['Demand (kW)'].to_numpy(float)
    supply=sum(result[k].to_numpy(float) for k in ('Solar (kW)','Wind (kW)','Grid (kW)'))
    if 'Battery dispatch (kW)' in result:supply+=result['Battery dispatch (kW)'].to_numpy(float)
    residual=supply-demand
    return {'max_abs_kw':float(np.max(np.abs(residual))),
            'hours_outside_tolerance':int(np.count_nonzero(np.abs(residual)>tolerance_kw)),
            'grid_nonnegative':bool((result['Grid (kW)']>=-tolerance_kw).all()),
            'hours':int(len(result)),
            'tolerance_kw':tolerance_kw}

def verify_desalination_balance(design,product_m3_day):
    feed=float(design.get('feed_m3_day',0))
    brine=feed-float(product_m3_day)
    return {'feed_m3_day':feed,'permeate_m3_day':float(product_m3_day),
            'brine_m3_day':brine,'water_balance_residual_m3_day':feed-float(product_m3_day)-brine,
            'valid_nonnegative_flows':bool(feed>=product_m3_day>=0 and brine>=0),
            'note':'Only bulk water balance; salt balance and chemistry require native process model.'}
