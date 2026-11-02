import requests
import pandas as pd
import numpy as np
from datetime import date
API='https://archive-api.open-meteo.com/v1/archive'
def get_weather(lat,lon,year):
    if year>=date.today().year:raise ValueError('Select a completed historical year.')
    p={'latitude':lat,'longitude':lon,'start_date':f'{year}-01-01','end_date':f'{year}-12-31','timezone':'GMT',
       'hourly':'temperature_2m,wind_speed_10m,shortwave_radiation,direct_normal_irradiance,diffuse_radiation'}
    r=requests.get(API,params=p,timeout=120);r.raise_for_status();raw=r.json();h=raw['hourly']
    df=pd.DataFrame({'time':h['time'],'temp_air':h['temperature_2m'],'wind_ms':np.asarray(h['wind_speed_10m'],dtype=float)/3.6,
                     'ghi':h['shortwave_radiation'],'dni':h['direct_normal_irradiance'],'dhi':h['diffuse_radiation']})
    if df.isna().any().any():raise ValueError('Incomplete weather records. Choose another year or location.')
    return df

def get_climatology(lat,lon,years=(2023,2024,2025)):
    """Multi-year mean hourly profile by month/day/hour; 8760 hours (leap day removed).
    Reconstructed 2025 timestamps are a representative climate year, not an observed 2025 record.
    """
    frames=[]
    for yr in years:
        w=get_weather(lat,lon,yr)
        t=pd.to_datetime(w['time'])
        w=w.loc[~((t.dt.month==2)&(t.dt.day==29))].copy()
        t=pd.to_datetime(w['time'])
        w['month']=t.dt.month;w['day']=t.dt.day;w['hour']=t.dt.hour
        frames.append(w)
    combined=pd.concat(frames,ignore_index=True)
    grouped=combined.groupby(['month','day','hour'],sort=True)[['temp_air','wind_ms','ghi','dni','dhi']].mean().reset_index()
    grouped['time']=pd.to_datetime(dict(year=2025,month=grouped.month,day=grouped.day,hour=grouped.hour)).dt.strftime('%Y-%m-%dT%H:%M')
    return grouped[['time','temp_air','wind_ms','ghi','dni','dhi']]


def get_design_temperatures(lat, lon, years=(2023,2024,2025)):
    """Empirical hourly dry-bulb percentiles, not certified ASHRAE weather."""
    temps=[]
    for year in years:
        frame=get_weather(lat,lon,year)
        temps.extend(frame['temp_air'].dropna().astype(float).tolist())
    if len(temps)<8000:raise ValueError('Insufficient historical hours')
    a=np.asarray(temps,dtype=float)
    return {'observed_min':float(a.min()),'heating_996':float(np.percentile(a,0.4)),
            'cooling_004':float(np.percentile(a,99.6)),'observed_max':float(a.max()),
            'years':list(years),'hour_count':len(a)}
