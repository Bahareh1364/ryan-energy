"""Direct combustion CO2 screening based on energy consumption on LHV basis.
Factors approximate IPCC 2006 default stationary combustion CO2 factors,
kg CO2 per kWh thermal LHV (TJ-to-kWh conversion). Not national inventory.
"""
FUELS={
 'natural_gas':{'label':'Natural gas','kg_co2_kwh':0.202},
 'gasoline':{'label':'Gasoline / petrol','kg_co2_kwh':0.249},
 'diesel':{'label':'Diesel / gasoil','kg_co2_kwh':0.267},
 'fuel_oil':{'label':'Heavy fuel oil / mazut','kg_co2_kwh':0.279},
 'kerosene':{'label':'Kerosene','kg_co2_kwh':0.257},
 'lpg':{'label':'LPG','kg_co2_kwh':0.227},
 'jet_fuel':{'label':'Jet fuel','kg_co2_kwh':0.258},
 'crude_oil':{'label':'Crude oil','kg_co2_kwh':0.264},
}
def direct_combustion_annual_tonnes(daily_kwh, factors=None,days=365):
 factors=factors or {k:v['kg_co2_kwh'] for k,v in FUELS.items()}
 return {fuel: max(0.,float(daily_kwh.get(fuel,0)))*float(factors[fuel])*days/1000 for fuel in FUELS}
