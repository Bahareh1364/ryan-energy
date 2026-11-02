def calculate_economics(pv_cost,wind_cost,generated_kwh,demand_kwh,grid_kwh,a):
 capex=pv_cost+wind_cost+a['extra_capex']
 baseline_energy=a['baseline_grid'] if a['baseline_grid']>0 else demand_kwh
 avoided_grid=max(0.,baseline_energy-grid_kwh) if generated_kwh is not None else 0.
 annual_benefit=avoided_grid*a['grid_purchase']+a['annual_other_benefit']+a['baseline_fuel']*a['fuel_price']
 annual_cost=capex*a['opex_pct']/100+a['annual_fixed']+a['fuel_heat']*a['fuel_price']
 net=annual_benefit-annual_cost
 cash=[-capex]+[net]*int(a['years'])
 npv=sum(v/(1+a['discount']/100)**i for i,v in enumerate(cash))
 payback=capex/net if net>0 else None
 generated=generated_kwh or 0.
 energy_discount=sum(generated/(1+a['discount']/100)**i for i in range(1,int(a['years'])+1))
 cost_discount=capex+sum(annual_cost/(1+a['discount']/100)**i for i in range(1,int(a['years'])+1))
 lcoe=cost_discount/energy_discount if energy_discount>0 else None
 return {'CAPEX':capex,'Annual net benefit':net,'NPV':npv,
  'Simple payback (years)':payback,'LCOE (currency/kWh)':lcoe,
  'Currency':a['currency'],'Annual cashflow':cash,'Lifetime (years)':int(a['years'])}
