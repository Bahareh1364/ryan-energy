"""Optional local/server API foundation; launch separately with uvicorn api_server:app.
This API intentionally exposes no arbitrary script execution or engine installation.
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from integrations import engine_status
from greenhouse_engine import greenhouse_heating
from desal_engine import estimate_desalination

app=FastAPI(title='RYAN ENERGY Simulation API',version='0.11.0')

@app.get('/health')
def health():
    status=engine_status()
    return {'service':'RYAN ENERGY','status':'ok',
            'engines':{k:bool(status[k]) for k in ('pvlib','PyPSA','EnergyPlus','WaterTAP')}}

class GreenhouseInput(BaseModel):
    structure:str=Field(pattern='^[ABC]$')
    span_width:float=Field(gt=0,le=500)
    length:float=Field(gt=0,le=5000)
    wall_height:float=Field(gt=0,le=100)
    roof_rise:float=Field(gt=0,le=100)
    spans:int=Field(ge=1,le=1000)
    structures:int=Field(ge=1,le=1000)
    u_value:float=Field(gt=0,le=50)
    air_changes:float=Field(ge=0,le=50)
    indoor_c:float=Field(ge=-30,le=70)
    outdoor_c:float=Field(ge=-80,le=70)

@app.post('/v1/greenhouse/screening')
def greenhouse_screening(q:GreenhouseInput):
    return {'model':'geometry-specific heating screening, not EnergyPlus',
            'result':greenhouse_heating(q.structure,q.span_width,q.length,q.wall_height,
                 q.roof_rise,q.spans,q.structures,q.u_value,q.air_changes,q.indoor_c,q.outdoor_c)}

class ROInput(BaseModel):
    product_m3_day:float=Field(ge=0,le=1e7)
    tds_mg_l:float=Field(ge=0,le=80000)
    recovery:float=Field(gt=0,lt=1)
    temperature_c:float=Field(ge=0,le=50)
    pump_eff:float=Field(gt=0,le=1)
    erd_eff:float=Field(ge=0,le=1)

@app.post('/v1/desalination/ro-screening')
def ro_screening(q:ROInput):
    return {'model':'RO screening, not WaterTAP',
            'result':estimate_desalination('RO',q.product_m3_day,q.tds_mg_l,
               q.recovery,q.temperature_c,q.pump_eff,q.erd_eff)}
