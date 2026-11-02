from pathlib import Path
import json
import numpy as np
import pandas as pd
import streamlit as st
from engine import pv_profile,wind_profile,design_count,economic_metrics,pypsa_dispatch
from desal_engine import estimate_desalination
from integrations import engine_status,run_energyplus,watertap_diagnostic,run_watertap_script
from greenhouse_energyplus import generate_greenhouse_idf
from watertap_ro import run_ro
from climate import get_climatology
from location_data import countries,provinces,cities,english_city
from demo_mode import synthetic_weather, validate_energy_balance, verify_desalination_balance

st.set_page_config(page_title='RYAN ENERGY | Energy Systems Studio',page_icon='⚡',layout='wide',initial_sidebar_state='expanded')
st.markdown("""<style>
.stApp{background:#f3f6fa}
.block-container{max-width:1500px;padding-top:1.4rem}
h1,h2,h3{color:#16354d}
div[data-testid="stMetric"]{background:#fff;border:1px solid #dde7ef;padding:16px;border-radius:12px}

/* Navigation tree: force dark surfaces at EVERY nesting level. */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]{
 background-color:#14283c!important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label{
 color:#eaf2f8!important;
}
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button,
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button[kind],
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stBaseButton-secondary"],
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stBaseButton-primary"]{
 display:flex!important;
 width:100%!important;
 justify-content:flex-start!important;
 text-align:left!important;
 background:#14283c!important;
 background-color:#14283c!important;
 background-image:none!important;
 border:0!important;
 border-radius:2px!important;
 box-shadow:none!important;
 color:#f4f8ff!important;
 min-height:31px!important;
 padding:3px 8px!important;
 margin:0!important;
 font-size:0.89rem!important;
 font-weight:500!important;
 opacity:1!important;
}
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button *,
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button p,
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button span{
 color:#f4f8ff!important;
 opacity:1!important;
 text-align:left!important;
}
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button:hover{
 background:#284963!important;
 background-color:#284963!important;
}
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stButton"] button:focus-visible{
 outline:2px solid #74b9ff!important;
}
section[data-testid="stSidebar"] .st-key-navtree [class*="st-key-child_"] button{
 padding-left:32px!important;
 font-weight:400!important;
 font-size:0.84rem!important;
}
section[data-testid="stSidebar"] .st-key-navtree .st-key-child_active button{
 background:#27577a!important;
 background-color:#27577a!important;
 border-left:3px solid #59b9ff!important;
}
section[data-testid="stSidebar"] .st-key-navtree [data-testid="stVerticalBlock"]{
 gap:0!important;
 row-gap:0!important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] *{color:#172c42!important}
section[data-testid="stSidebar"] [data-baseweb="select"]{background:#fff!important}

:root{color-scheme:light}
.stApp{background:linear-gradient(145deg,#f4f7fc 0%,#edf3f9 100%)!important}
.block-container{max-width:1540px!important;padding:1.6rem 2.5rem 3rem!important}
h1{font-weight:750!important;letter-spacing:-.035em!important;font-size:2.05rem!important}
h2,h3{letter-spacing:-.025em!important}
div[data-testid="stMetric"]{border:1px solid #d9e4ef!important;box-shadow:0 5px 20px rgba(19,52,85,.045)!important;border-radius:15px!important}
div[data-testid="stMetricValue"]{font-weight:700!important;color:#123f63!important}
section[data-testid="stSidebar"]{border-right:1px solid #23485f!important}
section[data-testid="stSidebar"] .st-key-navtree button{font-family:'Segoe UI',sans-serif!important}
section[data-testid="stSidebar"] .st-key-navtree [class*="st-key-child_"] button{padding-left:30px!important}
section[data-testid="stSidebar"] .st-key-navtree .st-key-child_active button{background-color:#245b80!important}
[data-testid="stAppViewContainer"] [data-testid="stVerticalBlockBorderWrapper"]:has(>div>div[data-testid="stVerticalBlock"]){border-radius:12px}
.stButton>button[kind="primary"]{background:#087eac!important;border:0!important;border-radius:8px!important;font-weight:600!important}
[data-baseweb="select"]>div{border-radius:8px!important}
[data-testid="stDataFrame"]{border-radius:12px!important;overflow:hidden}

/* Project actions at the bottom of the sidebar: high-contrast, readable controls. */
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stButton"] button,
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stDownloadButton"] button {
 background:#ffffff!important;
 color:#172c42!important;
 border:1px solid #a9bfd2!important;
 border-radius:8px!important;
 opacity:1!important;
 font-weight:650!important;
 min-height:39px!important;
}
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stButton"] button *,
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stDownloadButton"] button *{
 color:#172c42!important;
 opacity:1!important;
}
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stButton"] button:hover,
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stDownloadButton"] button:hover{
 background:#dbeefb!important;
 border-color:#58a1d3!important;
}
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stFileUploader"] button,
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stFileUploader"] button *{
 color:#172c42!important;
 opacity:1!important;
}
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stFileUploader"]{
 background:#f8fbff!important;
 border-radius:9px!important;
 padding:5px!important;
}
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stFileUploader"] small,
section[data-testid="stSidebar"] .st-key-project_file_actions [data-testid="stFileUploader"] span{
 color:#172c42!important;
}
</style>""",unsafe_allow_html=True)
ROOT=Path(__file__).parent
REF=json.loads((ROOT/'data/excel_reference.json').read_text(encoding='utf8'))
MENU={
 'Demand':['Heating & Cooling','Industry','Fuels','Transport','Desalination Demand'],
 'Supply':['Solar PV Design','Wind Farm Design','Greenhouse Design','Desalination Design','Storage & Grid'],
 'Economic Analysis':['Economics'],
 'Simulation':['Simulation']}
ALIASES={'Greenhouse Design':'Greenhouse','Storage & Grid':'Energy Supply & Dispatch','Desalination Design':'Desalination'}


# --- Persistent project UI: each engineering field has a stable identity. ---
import hashlib
from project_io import export_project, import_project

def project_input(kind, label, *args, **kwargs):
    field_id = kwargs.get('key') or ('project_' + hashlib.sha256((kind + ':' + str(label)).encode('utf-8')).hexdigest()[:18])
    kwargs['key'] = field_id
    stored = st.session_state.setdefault('_project_ui', {})
    if field_id in stored:
        old = stored[field_id]
        if kind == 'selectbox':
            options = args[0] if args else kwargs.get('options', [])
            try:
                kwargs['index'] = list(options).index(old)
            except (ValueError, TypeError):
                pass
        elif kind in ('number_input', 'text_input', 'checkbox'):
            kwargs['value'] = old
    value = getattr(st, kind)(label, *args, **kwargs)
    if isinstance(value, (str, int, float, bool)) or value is None:
        stored[field_id] = value
    return value

def restore_project_upload():
    upload = st.session_state.get('_project_upload')
    if upload is None:
        st.error('Choose a project JSON file first.')
        return
    try:
        state, fields = import_project(upload.getvalue())
        # Drop stale widget state before constructing the controls for this run.
        for key in list(st.session_state.keys()):
            if key != '_project_upload':
                del st.session_state[key]
        st.session_state.update(state)
        st.session_state['_project_ui'] = fields
        st.session_state['_project_loaded_message'] = 'Project loaded. Run Simulation to regenerate hourly results.'
        st.rerun()
    except Exception as exc:
        st.error('Could not load project: ' + str(exc))

st.session_state.setdefault('active_page','Simulation')
st.session_state.setdefault('expanded_menus',['Simulation'])
with st.sidebar:
 st.title('⚡ RYAN ENERGY');st.caption('ENERGY SYSTEMS STUDIO · v15.4')
 with st.container(key='navtree'):
  for group,items in MENU.items():
   expanded=group in st.session_state['expanded_menus']
   with st.container(key='parent_'+group.lower().replace(' ','_')):
    if st.button(('−  ' if expanded else '+  ')+group,key='group_'+group,use_container_width=True):
     if expanded:
      st.session_state['expanded_menus']=[g for g in st.session_state['expanded_menus'] if g!=group]
     else:
      st.session_state['expanded_menus']=[*st.session_state['expanded_menus'],group]
     st.rerun()
   if expanded:
    for item in items:
     active=st.session_state['active_page']==item
     with st.container(key='child_active' if active else 'child_'+item.lower().replace(' ','_').replace('&','and')):
      if st.button(('▸  ' if active else '   ')+item,key='nav_'+item,use_container_width=True):
       st.session_state['active_page']=item
       st.rerun()
 page=ALIASES.get(st.session_state['active_page'],st.session_state['active_page'])
 st.subheader('Project Location')
 options=countries();names=[n for n,c in options]
 country=project_input('selectbox','Country',names,index=names.index('Iran') if 'Iran' in names else 0)
 code=dict(options)[country]
 states=provinces(code)
 state_label=project_input('selectbox','Province / State',[name for name,_ in states]) if states else None
 state=dict(states).get(state_label) if state_label else None
 locs=cities(code,state) if state else []
 city_index=project_input('selectbox','City',range(len(locs)),format_func=lambda i:english_city(locs[i]['name'])) if locs else None
 loc=locs[city_index] if city_index is not None else None
 st.caption('New projects start with zero demand and installed capacity. Equipment specifications are editable engineering assumptions.')
 st.caption('Climate loads automatically when simulation starts')
 st.session_state['offline_demo']=project_input('checkbox','Offline demonstration (synthetic weather — not for engineering decisions)',value=st.session_state.get('offline_demo',False),help='Use only if internet is unavailable during the live demonstration.')
 st.divider()
 st.markdown('#### Project Files')
 st.caption('Save or reopen a project on this computer.')
 with st.container(key='project_file_actions'):
  try:
   _project_bytes_sidebar = export_project(st.session_state)
   st.download_button('Save Project JSON', data=_project_bytes_sidebar,
                      file_name='RYAN_ENERGY_project.json', mime='application/json',
                      use_container_width=True, key='_save_project_button')
  except Exception as _save_error:
   st.error('Project save failed: ' + str(_save_error))
  st.file_uploader('Load saved project (.json)', type=['json'], key='_project_upload')
  if st.button('Load Project', key='_load_project_button', use_container_width=True):
   restore_project_upload()
  if st.session_state.get('_project_loaded_message'):
   st.success(st.session_state.pop('_project_loaded_message'))
  if st.button('Reset Project — start from zero',use_container_width=True,key='reset_project'):
   st.session_state.clear()
   st.rerun()

st.title('RYAN ENERGY');st.caption('ENGINEERING DESIGN STUDIO  /  Solar · Wind · Greenhouse · Water · Storage · Economics')
if st.session_state.get('demo_mode'):
 st.warning('OFFLINE DEMONSTRATION MODE — synthetic climate, NOT measured weather and NOT validation data.')
if loc:
 lat,lon=float(loc['latitude']),float(loc['longitude'])
 year='2023–2025'
 st.caption(f"LOCATION  /  {english_city(loc['name']).upper()}  ·  {country.upper()}  /  {lat:.4f}°, {lon:.4f}°")
else:
 st.warning('Select a country, province and city in the sidebar.');st.stop()

@st.cache_data(ttl=86400,show_spinner=False)
def cached_weather(lat,lon):return get_climatology(lat,lon)
# Climate inputs are loaded automatically when the integrated simulation runs.
# The location selector in the sidebar is the only climate/location UI.
w=st.session_state.get('weather') if st.session_state.get('weather_key')==(lat,lon,year) else None
design=st.session_state.get('design_climate') if st.session_state.get('design_climate_key')==(lat,lon) else None

st.session_state.setdefault('pv_settings',{})
st.session_state.setdefault('wind_settings',{})
st.session_state.setdefault('demand_kw',0.)
st.session_state.setdefault('heating_electric_kw',0.)
st.session_state.setdefault('cooling_electric_kw',0.)
st.session_state.setdefault('industrial_electric_kw',0.)
st.session_state.setdefault('include_greenhouse',False)
st.session_state.setdefault('water_m3',0.)
st.session_state.setdefault('water_sec',4.)
st.session_state.setdefault('offline_demo',False)

if page=='Simulation':
 st.subheader('Integrated Energy System Simulation')
 st.caption('Configure the individual design modules, then calculate the combined electricity balance and economics.')
 c1,c2,c3,c4=st.columns(4)
 c1.metric('Solar PV capacity (kWp)',f"{st.session_state.get('pv_settings',{}).get('capacity',0):,.1f}")
 c2.metric('Wind turbines',str(st.session_state.get('wind_settings',{}).get('n',0)))
 c3.metric('Greenhouse heating (kW)',f"{st.session_state.get('greenhouse_heating_kw',0):,.1f}")
 c4.metric('Freshwater (m³/day)',f"{st.session_state.get('water_m3',0):,.0f}")
 st.info('Complete the left-hand input sections, then run the integrated system simulation here.')
 if st.button('Run Complete Simulation',type='primary',key='run_complete'):
  st.session_state['run_requested']=True

if page=='Solar PV Design':
 st.subheader('Solar PV Plant Design')
 mode=project_input('selectbox','Design Scenario',['Budget-Based','Land-Based','Equipment-Based'],index=['Budget-Based','Land-Based','Equipment-Based'].index(st.session_state.get('pv_design_mode','Equipment-Based')),key='pv_mode')
 st.session_state['pv_design_mode']=mode
 a,b,c=st.columns(3)
 with a:
  panel_w=project_input('number_input','Module rated power (W)',min_value=50.,value=float(st.session_state.get('pv_settings',{}).get('panel_w',550.)),step=25.)
  panel_area=project_input('number_input','Module area (m²)',min_value=0.1,value=2.6,step=0.1)
  tilt=project_input('number_input','Tilt (°)',min_value=0.,max_value=90.,value=float(st.session_state.get('pv_settings',{}).get('tilt',30.)))
  azimuth=project_input('number_input','Azimuth (°; south = 180)',min_value=0.,max_value=360.,value=float(st.session_state.get('pv_settings',{}).get('azimuth',180.)))
 with b:
  gamma=project_input('number_input','Power temperature coefficient (%/°C)',value=float(st.session_state.get('pv_settings',{}).get('gamma',-0.0035))*100,step=0.05)
  losses=project_input('number_input','Other DC losses (%)',min_value=0.,max_value=60.,value=float(st.session_state.get('pv_settings',{}).get('losses',0.14))*100)
  inverter_eff=project_input('number_input','Inverter efficiency (%)',min_value=50.,max_value=100.,value=float(st.session_state.get('pv_settings',{}).get('inverter_eff',0.96))*100)
  ground_factor=project_input('number_input','Land multiplier (site area / panel area)',min_value=1.,value=2.5,step=0.1)
 with c:
  unit_cost=project_input('number_input','Installed cost per panel (project currency)',min_value=1.,value=20000000.,step=1000000.)
  fixed_cost=project_input('number_input','Fixed project cost (project currency)',min_value=0.,value=0.,step=1000000.)
  if mode=='Budget-Based':
   budget=project_input('number_input','Maximum investment budget',min_value=0.,value=0.,step=100000000.)
   land=0;count=0
   st.caption('Land and module count are calculated outputs in this scenario.')
  elif mode=='Land-Based':
   land=project_input('number_input','Maximum available land (m²)',min_value=0.,value=0.,step=100.)
   budget=0;count=0
   st.caption('Budget and module count are calculated outputs in this scenario.')
  else:
   count=project_input('number_input','Fixed number of PV modules',min_value=0,value=int(st.session_state.get('pv_settings',{}).get('n',0)),step=10,key='pv_module_count')
   budget=0;land=0
   st.caption('Budget and required land are calculated outputs in this scenario.')
 n=design_count(mode,budget,land,count,unit_cost,fixed_cost,panel_area*ground_factor)
 capacity=n*panel_w/1000;cost=fixed_cost+n*unit_cost
 st.session_state['pv_settings']={'n':n,'panel_w':panel_w,'tilt':tilt,'azimuth':azimuth,'gamma':gamma/100,'losses':losses/100,'inverter_eff':inverter_eff/100,'cost':cost,'area':n*panel_area*ground_factor,'capacity':capacity}
 m1,m2,m3=st.columns(3);m1.metric('PV modules',f'{n:,}');m2.metric('DC capacity (kWp)',f'{capacity:,.1f}');m3.metric('Estimated land (m²)',f'{n*panel_area*ground_factor:,.0f}')
 st.caption('Panel price and land multiplier are editable planning assumptions, not market quotations or detailed layout.')

if page=='Wind Farm Design':
 st.subheader('Wind Farm Design')
 mode=project_input('selectbox','Design Scenario',['Budget-Based','Land-Based','Equipment-Based'],index=2,key='wind_mode')
 a,b,c=st.columns(3)
 with a:
  rated_kw=project_input('number_input','Turbine rated power (kW)',min_value=1.,value=3000.)
  hub=project_input('number_input','Hub height (m)',min_value=10.,value=100.)
  diameter=project_input('number_input','Rotor diameter (m)',min_value=1.,value=120.)
  alpha=project_input('number_input','Wind shear exponent (assumption)',min_value=0.,max_value=1.,value=0.14,step=0.01)
 with b:
  cutin=project_input('number_input','Cut-in speed (m/s)',min_value=0.1,value=3.)
  rated_ms=project_input('number_input','Rated speed (m/s)',min_value=1.,value=12.)
  cutout=project_input('number_input','Cut-out speed (m/s)',min_value=1.,value=25.)
  wind_losses=project_input('number_input','Combined wake / availability losses (%)',min_value=0.,max_value=80.,value=16.)
 with c:
  unit_cost=project_input('number_input','Installed cost per turbine (project currency)',min_value=1.,value=200000000000.,step=1000000000.)
  fixed_cost=project_input('number_input','Fixed project cost (project currency)',min_value=0.,value=0.,step=100000000.)
  spacing=project_input('number_input','Spacing multiplier (rotor diameters × rotor diameters)',min_value=1.,value=35.,step=1.)
  if mode=='Budget-Based':
   budget=project_input('number_input','Maximum wind project budget',min_value=0.,value=0.,step=10000000000.)
   land=0;count=0
   st.caption('Land and turbine count are calculated outputs.')
  elif mode=='Land-Based':
   land=project_input('number_input','Maximum wind farm land (m²)',min_value=0.,value=0.,step=10000.)
   budget=0;count=0
   st.caption('Budget and turbine count are calculated outputs.')
  else:
   count=project_input('number_input','Fixed number of wind turbines',min_value=0,value=int(st.session_state.get('wind_settings',{}).get('n',0)),key='wind_turbine_count')
   budget=0;land=0
   st.caption('Budget and required land are calculated outputs.')
 curve_file=st.file_uploader('Manufacturer power curve CSV (optional): wind_ms, power_kw',type=['csv'],key='curve')
 curve=None
 if curve_file:
  try:
   curve=pd.read_csv(curve_file)
   if not {'wind_ms','power_kw'}.issubset(curve.columns):raise ValueError('Columns wind_ms, power_kw required.')
   curve=curve[['wind_ms','power_kw']].astype(float).dropna()
   if len(curve)<2:raise ValueError('At least two power-curve points are required.')
  except Exception as e:st.error(str(e));curve=None
 n=design_count(mode,budget,land,count,unit_cost,fixed_cost,spacing*diameter**2)
 st.session_state['wind_settings']={'n':n,'rated_kw':rated_kw,'hub':hub,'diameter':diameter,'alpha':alpha,'cutin':cutin,'rated_ms':rated_ms,'cutout':cutout,'losses':wind_losses/100,'cost':fixed_cost+n*unit_cost,'area':n*spacing*diameter**2,'curve':curve}
 a,b,c=st.columns(3);a.metric('Turbines',f'{n:,}');b.metric('Capacity (MW)',f'{n*rated_kw/1000:,.2f}');c.metric('Planning footprint (ha)',f'{n*spacing*diameter**2/10000:,.1f}')
 st.warning('Land spacing is a screening approximation, not a wind-farm micrositing study. Without a manufacturer curve, a cubic surrogate is used.')

if page=='Heating & Cooling':
 st.subheader('Demand · Heating & Cooling')
 st.caption('Electricity and thermal energy are tracked separately. All entries are preliminary constant loads.')
 a,b=st.columns(2)
 with a:
  st.session_state['demand_kw']=project_input('number_input','Other / base electricity demand (kW)',min_value=0.,value=float(st.session_state['demand_kw']),step=10.)
  st.session_state['heating_electric_kw']=project_input('number_input','Electric heating demand (kW)',min_value=0.,value=float(st.session_state['heating_electric_kw']))
  st.session_state['heat_thermal_kw']=project_input('number_input','Thermal heating demand (kWₜₕ)',min_value=0.,value=float(st.session_state.get('heat_thermal_kw',0.)))
 with b:
  st.session_state['cooling_electric_kw']=project_input('number_input','Electric cooling demand (kW)',min_value=0.,value=float(st.session_state['cooling_electric_kw']))
  st.session_state['cool_thermal_kw']=project_input('number_input','Thermal cooling demand (kWₜₕ)',min_value=0.,value=float(st.session_state.get('cool_thermal_kw',0.)))
 st.session_state['include_greenhouse']=project_input('checkbox','Include greenhouse design heating via electric heat pump',value=st.session_state['include_greenhouse'])
 if st.session_state['include_greenhouse']:
  st.session_state['greenhouse_cop']=project_input('number_input','Heat pump COP',min_value=1.,max_value=10.,value=float(st.session_state.get('greenhouse_cop',3.)),step=0.1)
 st.caption('Thermal loads are reported separately until fuel/heat conversion and hourly load profiles are modeled.')

if page=='Industry':
 st.subheader('Demand · Industry')
 st.session_state['industrial_electric_kw']=project_input('number_input','Industrial process electricity (kW)',min_value=0.,value=float(st.session_state['industrial_electric_kw']))
 st.session_state['industry_heat_kw']=project_input('number_input','Industrial process heat (kWₜₕ)',min_value=0.,value=float(st.session_state.get('industry_heat_kw',0.)))
 st.caption('Industrial process heat is recorded as thermal demand; it is not automatically counted as electricity.')

if page=='Fuels':
 st.subheader('Demand · Fuels')
 st.caption('Enter fuel consumption by fuel type as thermal energy (kWh LHV/day). No fuel conversion or fuel-fired generation is inferred.')
 from emissions import FUELS
 cols=st.columns(2)
 for i,(fuel,meta) in enumerate(FUELS.items()):
  with cols[i%2]:
   st.session_state['fuel_'+fuel]=project_input('number_input',
     f"{meta['label']} (kWh LHV/day)",min_value=0.,
     value=float(st.session_state.get('fuel_'+fuel,0.)),step=100.,
     key='input_fuel_'+fuel)
 st.caption('CO₂ factors are illustrative direct-combustion factors; user can edit them in Simulation. This is not a full lifecycle or national inventory.')

if page=='Transport':
 st.subheader('Demand · Transport')
 st.session_state['transport_ev_kwh_day']=project_input('number_input','Electric transport demand (kWh/day)',min_value=0.,value=float(st.session_state.get('transport_ev_kwh_day',0.)))
 st.session_state['transport_fuel_kwh_day']=project_input('number_input','Transport fuel energy (kWh thermal/day)',min_value=0.,value=float(st.session_state.get('transport_fuel_kwh_day',0.)))
 st.caption('Electric transport energy is represented as a constant hourly average until a charging schedule is supplied.')

if page=='Desalination Demand':
 st.subheader('Demand · Desalination')


if page=='Desalination':
 st.subheader('Desalination Plant Design')
 st.caption('RO: feed/brine/permeate balance, osmotic pressure, net driving pressure and membrane-area estimate. Thermal methods: explicit stage-effect screening.')
 tech=project_input('selectbox','Desalination technology',['RO — Reverse Osmosis','MED — Multi-Effect Distillation','MSF — Multi-Stage Flash'])
 a,b,c=st.columns(3)
 with a:
  flow=project_input('number_input','Freshwater production (m³/day)',min_value=0.,value=float(st.session_state['water_m3']),step=100.)
  sal=project_input('number_input','Feedwater salinity (mg/L TDS)',min_value=0.,max_value=80000.,value=35000.,step=1000.)
 with b:
  recovery=project_input('number_input','Recovery ratio (%)',min_value=5.,max_value=85.,value=45.,step=1.)
  feed_temp=project_input('number_input','Feedwater temperature (°C)',min_value=0.,max_value=50.,value=25.)
 with c:
  pump_eff=project_input('number_input','Pump efficiency (%)',min_value=30.,max_value=95.,value=80.)
  erd_eff=project_input('number_input','Energy recovery efficiency (%) — RO only',min_value=0.,max_value=95.,value=85.,disabled=not tech.startswith('RO'))
 if tech.startswith('RO'):
  r1,r2,r3=st.columns(3)
  with r1: membrane_perm=project_input('number_input','Membrane permeability A (L/m²/h/bar)',min_value=0.1,max_value=20.,value=1.5,step=0.1)
  with r2: fouling=project_input('number_input','Membrane fouling allowance (%)',min_value=0.,max_value=70.,value=15.)
  with r3: product_tds=project_input('number_input','Target permeate TDS (mg/L)',min_value=0.,max_value=5000.,value=300.)
  effects=8;gor=8.
 else:
  r1,r2=st.columns(2)
  with r1:effects=project_input('number_input','Number of effects / stages',min_value=2,max_value=40,value=8 if tech.startswith('MED') else 18)
  with r2:gor=project_input('number_input','Gained output ratio (kg distillate / kg steam)',min_value=1.,max_value=25.,value=7. if tech.startswith('MED') else 8.)
  membrane_perm=1.5;fouling=15.;product_tds=300.
 outcome=estimate_desalination(tech.split(' ')[0],flow,sal,recovery/100,feed_temp,pump_eff/100,erd_eff/100,membrane_perm,fouling/100,product_tds,effects,gor)
 st.session_state['water_m3']=flow
 st.session_state['water_sec']=outcome['electric_sec']
 st.session_state['desal_design']={'Technology':tech.split(' ')[0],**outcome}
 st.session_state['desal_inputs']={'product_m3_day':flow,'tds_mg_l':sal,'recovery':recovery/100,'temperature_c':feed_temp,'pressure_bar':float(outcome.get('design_pressure_bar') or 60.),'membrane_area_m2':max(1.,float(outcome.get('membrane_area_m2') or 1.)),'water_permeability_m_pa_s':membrane_perm/3.6e11,'salt_permeability_m_s':1e-8}
 d1,d2,d3=st.columns(3)
 d1.metric('Electricity (kWh/day)',f"{outcome['electric_day']:,.0f}")
 d2.metric('Thermal energy (kWhₜₕ/day)',f"{outcome['thermal_day']:,.0f}")
 d3.metric('Feedwater (m³/day)',f"{outcome['feed_m3_day']:,.0f}")
 st.dataframe(pd.DataFrame([{'Technology':tech,'Feed salinity (mg/L)':sal,'Recovery (%)':recovery,**outcome}]),hide_index=True,use_container_width=True)
 st.warning(outcome['note'])
 st.caption('MED/MSF thermal input is tracked separately from electricity. This is NOT an IDAES/WaterTAP simulation; detailed equipment and seawater chemistry still require verification.')
 # WaterTAP is a backend solver dependency, not a separate user-facing workflow.
 # Native results will be shown within the same desalination result panel if available.
 if tech.startswith('RO') and st.session_state.get('watertap_result'):
  with st.expander('Advanced validated solver details'):
   st.json(st.session_state['watertap_result'])

if page in ('Energy Supply & Dispatch','Simulation'):
 if page!='Simulation':st.subheader('Storage & Grid Settings')
 st.caption('Configure storage and grid assumptions here; the integrated PyPSA dispatch runs in Simulation.')
 grid_cost=project_input('number_input','Grid marginal cost (project currency/kWh)',min_value=0.,value=0.,step=100.,key='grid_marginal_cost')
 battery_kwh=project_input('number_input','Battery energy capacity (kWh)',min_value=0.,value=float(st.session_state.get('battery_energy_kwh',0.)),step=50.)
 st.session_state['battery_energy_kwh']=battery_kwh
 battery_kw=project_input('number_input','Battery power (kW)',min_value=0.,value=0.,step=10.,key='battery_power_kw')
 battery_eff=project_input('number_input','Battery round-trip efficiency (%)',min_value=1.,max_value=100.,value=90.,key='battery_efficiency_pct')
 st.caption('Grid backup is limited to twice demand; this is an operational dispatch model with fixed capacities, not network power flow or investment optimization.')
 if (False if page!='Simulation' else st.session_state.pop('run_requested',False)):
  w=st.session_state.get('weather') if (st.session_state.get('weather_key')==(lat,lon,year) and (st.session_state.get('offline_demo') or not st.session_state.get('demo_mode'))) else None
  if st.session_state.get('offline_demo'):
   w=synthetic_weather(lat,lon)
   st.session_state['demo_mode']=True
   st.session_state['weather']=w
   st.session_state['weather_key']=(lat,lon,year)
  if w is None:
   try:
    with st.spinner('Retrieving climate data for the selected location...'):
     w=cached_weather(round(lat,4),round(lon,4))
    st.session_state['weather']=w
    st.session_state['weather_key']=(lat,lon,year)
    st.session_state['demo_mode']=False
   except Exception as exc:
    st.error(f'Unable to load climate data: {exc}. Check internet connection and try again.')
  if w is not None:
   try:
    p=st.session_state['pv_settings'];v=st.session_state['wind_settings']
    if not p and not v:raise ValueError('Configure at least one Solar PV or Wind Farm design first.')
    with st.spinner('Calculating pvlib solar production, wind output, and PyPSA dispatch...'):
     solar=(pv_profile(w,lat,lon,p['tilt'],p['azimuth'],p['panel_w'],p['n'],p['gamma'],p['losses'],p['inverter_eff']) if p else pd.Series(np.zeros(len(w))))
     wind=(wind_profile(w,v['rated_kw'],v['n'],v['hub'],v['cutin'],v['rated_ms'],v['cutout'],v['alpha'],v['losses'],v['curve']) if v else pd.Series(np.zeros(len(w))))
     load=(st.session_state['demand_kw']+st.session_state['industrial_electric_kw']+st.session_state['heating_electric_kw']+st.session_state['cooling_electric_kw']+st.session_state['water_m3']*st.session_state['water_sec']/24+st.session_state.get('transport_ev_kwh_day',0.)/24)
     if st.session_state['include_greenhouse']:
      load+=st.session_state.get('greenhouse_heating_kw',0)/st.session_state.get('greenhouse_cop',3.)
     result=pypsa_dispatch(w,solar,wind,load,grid_cost,battery_kwh,battery_kw,battery_eff/100)
    st.session_state['dispatch']=result;st.session_state['dispatch_location']=(lat,lon,year)
    st.success('Energy system simulation completed successfully.')
    if st.session_state.get('demo_mode'):st.warning('Results use SYNTHETIC demonstration weather. Do not use these outputs for investment or engineering validation.')
   except Exception as e:st.error(f'Simulation failed: {e}')

if page=='Simulation':
 st.caption('Displayed simulation results are from the last Run Complete Simulation. Rerun after editing inputs.')
 result=st.session_state.get('dispatch') if st.session_state.get('dispatch_location')==(lat,lon,year) else None
 if result is None:st.info('Configure Demand, Supply, Greenhouse, Desalination and Storage, then run the simulation to view the integrated results.')
 else:
  if page!='Economics':
   st.subheader('Hourly Energy Balance')
   total_demand=result['Demand (kW)'].sum();solar=result['Solar (kW)'].sum();wind=result['Wind (kW)'].sum();grid=result['Grid (kW)'].sum()
   a,b,c,d=st.columns(4);a.metric('Demand (MWh)',f'{total_demand/1000:,.1f}');b.metric('Solar (MWh)',f'{solar/1000:,.1f}');c.metric('Wind (MWh)',f'{wind/1000:,.1f}');d.metric('Grid (MWh)',f'{grid/1000:,.1f}')
   balance=validate_energy_balance(result)['max_abs_kw']
   st.metric('Max hourly power balance residual (kW)',f'{balance:.6f}')
   st.line_chart(result[['Demand (kW)','Solar (kW)','Wind (kW)','Grid (kW)']].iloc[:168]);st.caption('Chart shows the first 168 hours. CSV contains the full modeled year.')
   st.download_button('Download Hourly Results CSV',result.to_csv(index_label='time').encode('utf-8-sig'),file_name='RYAN_ENERGY_hourly_results.csv',mime='text/csv')
  else:
   pass

if page=='Simulation':
 st.subheader('Integrated Supply Overview')
 pv=st.session_state.get('pv_settings',{})
 wi=st.session_state.get('wind_settings',{})
 st.dataframe(pd.DataFrame([
  {'Supply / asset':'Solar PV','Capacity / design':f"{pv.get('capacity',0):,.1f} kWp"},
  {'Supply / asset':'Wind farm','Capacity / design':f"{wi.get('n',0)*wi.get('rated_kw',0):,.1f} kW"},
  {'Supply / asset':'Greenhouse','Capacity / design':f"{st.session_state.get('greenhouse_area_m2',0):,.1f} m²"},
  {'Supply / asset':'Desalination','Capacity / design':f"{st.session_state.get('water_m3',0):,.1f} m³/day"},
  {'Supply / asset':'Battery storage','Capacity / design':f"{st.session_state.get('battery_energy_kwh',0):,.1f} kWh"},
 ]),hide_index=True,use_container_width=True)
 st.subheader('Integrated Demand Overview')
 st.dataframe(pd.DataFrame([
  {'Sector':'Base electricity','Demand':'%.1f kW'%st.session_state['demand_kw']},
  {'Sector':'Industry electricity','Demand':'%.1f kW'%st.session_state['industrial_electric_kw']},
  {'Sector':'Heating electricity','Demand':'%.1f kW'%st.session_state['heating_electric_kw']},
  {'Sector':'Cooling electricity','Demand':'%.1f kW'%st.session_state['cooling_electric_kw']},
  {'Sector':'Industrial thermal heat','Demand':'%.1f kWth'%st.session_state.get('industry_heat_kw',0.)},
  *[{'Sector':meta['label'],'Demand':'%.1f kWhth/day'%st.session_state.get('fuel_'+fuel,0.)}
    for fuel,meta in __import__('emissions').FUELS.items()],
  {'Sector':'Transport electricity','Demand':'%.1f kWh/day'%st.session_state.get('transport_ev_kwh_day',0.)},
  {'Sector':'Transport fuels','Demand':'%.1f kWhth/day'%st.session_state.get('transport_fuel_kwh_day',0.)},
  {'Sector':'Desalination electricity','Demand':'%.1f kWh/day'%(st.session_state['water_m3']*st.session_state['water_sec'])},
 ]),hide_index=True,use_container_width=True)
 if st.session_state.get('greenhouse_design'):
  st.subheader('Greenhouse Summary')
  st.dataframe(pd.DataFrame([st.session_state['greenhouse_design']]),hide_index=True,use_container_width=True)
 if st.session_state.get('desal_design'):
  st.subheader('Desalination Summary')
  st.dataframe(pd.DataFrame([st.session_state['desal_design']]),hide_index=True,use_container_width=True)
 econ=st.session_state.get('economics_summary')
 if st.session_state.get('economics_inputs'):
  from economic_reporting import calculate_economics
  sim=st.session_state.get('dispatch') if st.session_state.get('dispatch_location')==(lat,lon,year) else None
  econ=calculate_economics(st.session_state['pv_settings'].get('cost',0),
    st.session_state['wind_settings'].get('cost',0),
    float(sim['Solar (kW)'].sum()+sim['Wind (kW)'].sum()) if sim is not None else None,
    float(sim['Demand (kW)'].sum()) if sim is not None else 0.,
    float(sim['Grid (kW)'].sum()) if sim is not None else 0.,
    st.session_state['economics_inputs'])
  st.session_state['economics_summary']=econ
 if econ:
  st.subheader('Economic Results')
  aa,bb,cc,dd=st.columns(4)
  aa.metric('CAPEX',f"{econ['CAPEX']:,.0f} {econ['Currency']}")
  bb.metric('Annual net benefit',f"{econ['Annual net benefit']:,.0f}")
  cc.metric('NPV',f"{econ['NPV']:,.0f}")
  dd.metric('Simple payback',f"{econ['Simple payback (years)']:.1f} years" if econ['Simple payback (years)'] is not None else 'Not achieved')
  if econ['LCOE (currency/kWh)'] is not None:st.metric('LCOE',f"{econ['LCOE (currency/kWh)']:,.2f}")
  st.line_chart(pd.DataFrame({'Year':range(econ['Lifetime (years)']+1),'Cumulative cashflow':np.cumsum(econ['Annual cashflow'])}).set_index('Year'))
  st.caption('Economics recalculated from current dispatch and saved economic assumptions.')

if page=='Simulation':
 from emissions import FUELS,direct_combustion_annual_tonnes
 st.subheader('Carbon Emissions · Direct Combustion & Grid Electricity')
 st.caption('Indicative annual CO₂ only (not CO₂e). Fuel quantities use LHV; default factors are editable assumptions approximating IPCC default stationary combustion factors.')
 with st.expander('Emission factor assumptions (kg CO₂/kWh LHV)',expanded=False):
  factors={}
  for fuel,meta in FUELS.items():
   factors[fuel]=project_input('number_input',meta['label']+' emission factor',min_value=0.,max_value=5.,
      value=float(st.session_state.get('ef_'+fuel,meta['kg_co2_kwh'])),
      step=0.001,format='%.3f',key='ef_input_'+fuel)
   st.session_state['ef_'+fuel]=factors[fuel]
  grid_factor=project_input('number_input','Grid emission factor (kg CO₂/kWh electricity)',
     min_value=0.,max_value=3.,value=float(st.session_state.get('grid_emission_factor',0.0)),
     step=0.01,format='%.3f')
  st.session_state['grid_emission_factor']=grid_factor
  st.caption('Grid factor default 0.5 is an illustrative placeholder, not a verified Iranian grid factor.')
 daily={k:st.session_state.get('fuel_'+k,0.) for k in FUELS}
 direct=direct_combustion_annual_tonnes(daily,factors)
 # Separate transport fuel demand is an aggregate with unknown composition.
 # Do not assign a fuel factor or count it twice.
 grid_mwh=0.
 sim=st.session_state.get('dispatch') if st.session_state.get('dispatch_location')==(lat,lon,year) else None
 if sim is not None:
  grid_mwh=float(sim['Grid (kW)'].sum())/1000.
 grid_co2=grid_mwh*1000*st.session_state.get('grid_emission_factor',0.0)/1000
 carbon_df=pd.DataFrame([{'Source':FUELS[k]['label'],'Annual CO₂ (tonnes)':round(v,2)} for k,v in direct.items()]
     +[{'Source':'Purchased grid electricity','Annual CO₂ (tonnes)':round(grid_co2,2)}])
 st.dataframe(carbon_df,hide_index=True,use_container_width=True)
 c1,c2,c3=st.columns(3)
 c1.metric('Fuel CO₂ (t/year)',f'{sum(direct.values()):,.1f}')
 c2.metric('Grid CO₂ (t/year)',f'{grid_co2:,.1f}' if sim is not None else 'Not calculated')
 c3.metric('Total estimated CO₂ (t/year)',f'{sum(direct.values())+grid_co2:,.1f}' if sim is not None else 'Pending dispatch')
 st.bar_chart(carbon_df.set_index('Source'))
 st.download_button('Download Carbon Inventory (CSV)',
   carbon_df.to_csv(index=False).encode('utf-8-sig'),file_name='RYAN_ENERGY_CO2_Inventory.csv',mime='text/csv')
 if st.session_state.get('transport_fuel_kwh_day',0)>0:
  st.warning('Transport fuel demand is not included in CO₂ totals because its fuel composition is unspecified. Enter gasoline/diesel quantities under Demand → Fuels; do not double-count.')
 if sim is None:
  st.info('Grid CO₂ will be calculated after running the electricity dispatch. Current grid CO₂ is not available.')
 st.caption('Excludes upstream emissions, non-CO₂ greenhouse gases, process emissions, exported electricity credits and detailed technology lifecycle emissions.')

if page=='Economics':
 result=st.session_state.get('dispatch') if st.session_state.get('dispatch_location')==(lat,lon,year) else None
 st.subheader('Project Economics · Cost–Benefit Analysis')
 st.caption('Enter prices and assumptions; the model calculates capital cost, annual cash flow, NPV, LCOE and simple payback. Generation benefits require a completed simulation.')
 a,b,c=st.columns(3)
 with a:
  currency=project_input('text_input','Project currency',value='IRR')
  tariff=project_input('number_input','Electricity value / sale tariff (currency/kWh)',min_value=0.,value=0.,step=100.)
  fuel_price=project_input('number_input','Fuel price (currency/kWh thermal)',min_value=0.,value=0.,step=100.)
  fuel_heat=project_input('number_input','Annual fuel consumption (kWh thermal)',min_value=0.,value=0.,step=1000.)
 with b:
  grid_purchase=project_input('number_input','Grid purchase price (currency/kWh)',min_value=0.,value=0.,step=100.)
  extra_capex=project_input('number_input','Other technology / desalination / greenhouse CAPEX',min_value=0.,value=0.,step=1000000.)
  opex_pct=project_input('number_input','Annual OPEX (% of total CAPEX)',min_value=0.,value=0.,step=0.5)
  annual_fixed=project_input('number_input','Other annual fixed cost',min_value=0.,value=0.,step=100000.)
 with c:
  years=project_input('number_input','Project lifetime (years)',min_value=1,max_value=50,value=20)
  discount=project_input('number_input','Discount rate (%)',min_value=0.,max_value=100.,value=12.)
  annual_other_benefit=project_input('number_input','Other annual benefits / water revenue',min_value=0.,value=0.,step=100000.)
  baseline_fuel=project_input('number_input','Avoided baseline fuel use (kWh thermal/year)',min_value=0.,value=0.,step=1000.)
 baseline_grid=project_input('number_input','Baseline grid electricity consumption (kWh/year; 0 = same modeled demand)',min_value=0.,value=0.,step=1000.)
 st.session_state['economics_inputs']={
  'currency':currency,'tariff':tariff,'fuel_price':fuel_price,'fuel_heat':fuel_heat,
  'grid_purchase':grid_purchase,'extra_capex':extra_capex,'opex_pct':opex_pct,
  'annual_fixed':annual_fixed,'years':years,'discount':discount,
  'annual_other_benefit':annual_other_benefit,'baseline_fuel':baseline_fuel,
  'baseline_grid':baseline_grid}
 from economic_reporting import calculate_economics
 st.session_state['economics_summary']=calculate_economics(
  st.session_state['pv_settings'].get('cost',0),
  st.session_state['wind_settings'].get('cost',0),
  float(result['Solar (kW)'].sum()+result['Wind (kW)'].sum()) if result is not None else None,
  float(result['Demand (kW)'].sum()) if result is not None else 0.,
  float(result['Grid (kW)'].sum()) if result is not None else 0.,
  st.session_state['economics_inputs'])
 st.info('Economic assumptions saved. Results and charts are displayed only under Simulation.')

if page=='Greenhouse':
 st.subheader('Greenhouse Engineering Design')
 st.caption('Integrated preliminary sizing: heating, cooling, ventilation, irrigation and crop lighting. Results appear below and are downloadable; no separate EnergyPlus output is required.')
 CROP_EN={'گوجه فرنگی':'Tomato','مرکبات':'Citrus','فلفل':'Pepper','هویج':'Carrot','کاهو':'Lettuce','سیب زمینی':'Potato','پیاز':'Onion','خیار':'Cucumber','کلم':'Cabbage','بروکلی':'Broccoli','توت فرنگی':'Strawberry','گل اونتاریم':'Anthurium','گل داوودی':'Chrysanthemum','گل شمعدانی':'Geranium','گل رز':'Rose','گل لیلیوم':'Lily','گل سوسن':'Iris','گل میخک':'Carnation','گل ارکیده':'Orchid'}
 COVER_EN={
 'سطح لعابی با قاب فلزی به فاصله 400 تا 600 میلیمتر':'Glazed surface, metal frame (400–600 mm spacing)',
 'سطح لعابی با قاب فلزی به فاصله 1200 میلیمتر':'Glazed surface, metal frame (1200 mm spacing)',
 'فایبر گلاس در قاب فلزی':'Fiberglass in metal frame',
 'فیلم پلاستیک در قاب فلزی':'Plastic film in metal frame'}
 crop_names=sorted(REF['crops'],key=lambda x:CROP_EN.get(x,x))
 a,b=st.columns([1,1.15])
 with a:
  st.markdown('#### Crop & Structure')
  crop=project_input('selectbox','Crop',crop_names,format_func=lambda x:CROP_EN.get(x,'Crop '+str(crop_names.index(x)+1)))
  comfort=project_input('selectbox','Crop comfort temperature (°C)',REF['crops'][crop])
  structure=project_input('selectbox','Structure Type',['A','B','C'],key='structure_type')
  st.caption('Select A, B or C to display the corresponding workbook structure.')
  images={'A':'image1.png','B':'image2.png','C':'image3.png'}
  st.image(str(ROOT/'assets'/images[structure]),caption='Original reference diagram from GREEN HOUSE.xlsx — '+structure,use_container_width=True)
  st.caption('Dimension labels a, b, c and h refer to the letters on the selected workbook diagram. Check their meaning for each geometry.')
 with b:
  st.markdown('#### Dimensions & Configuration')
  col1,col2=st.columns(2)
  with col1:
   span_width=project_input('number_input','a — Span width (m)',min_value=1.,value=8.)
   length=project_input('number_input','b — Structure length (m)',min_value=1.,value=40.)
   height=project_input('number_input','h — Wall / reference height (m)',min_value=0.5,value=4.)
  with col2:
   spans=project_input('number_input','Number of spans',min_value=1,value=3)
   structures=project_input('number_input','Number of structures',min_value=1,value=1)
   arch_rise=project_input('number_input','c — Roof rise / roof reference (m)',min_value=0.1,value=2.)
  cover_names=list(REF['covers'])
  cover=project_input('selectbox','Covering Material',cover_names,format_func=lambda x:COVER_EN.get(x,'Cover type '+str(cover_names.index(x)+1)))
  U=float(REF['covers'][cover]);st.caption(f'Reference workbook covering coefficient: {U:g} (unit must be verified)')
  air_changes=project_input('number_input','Air exchange rate (1/h)',min_value=0.,value=1.,step=0.1)
  design_climate=st.session_state.get('design_climate') if st.session_state.get('design_climate_key')==(lat,lon) else None
  if design_climate:
   temp_method=project_input('selectbox','Heating design temperature basis',['Observed historical minimum','99.6% hourly heating percentile','Manual override'])
   default_t=(design_climate['observed_min'] if temp_method.startswith('Observed') else design_climate['heating_996'])
   design_out=project_input('number_input','Outdoor heating design temperature (°C)',value=float(round(default_t,1)),disabled=not temp_method.startswith('Manual'),key='gh_design_out_'+temp_method)
   st.caption('Derived from raw historical temperatures, not multi-year hourly averages.')
  else:
   st.warning('Heating outdoor design temperature is a MANUAL assumption until verified site design climate data are available.')
   design_out=project_input('number_input','Manual outdoor heating design temperature (°C)',value=-4.)
 st.markdown('#### Design Results')
 from greenhouse_engine import greenhouse_heating
 calculation=greenhouse_heating(structure,span_width,length,height,arch_rise,spans,structures,U,air_changes,float(comfort),design_out)
 footprint=calculation['floor_area_m2'];volume=calculation['volume_m3']
 q_cond=calculation['transmission_kw'];q_vent=calculation['infiltration_kw'];heating=calculation['heating_kw']
 st.session_state['greenhouse_heating_kw']=heating
 st.session_state['greenhouse_area_m2']=footprint
 st.session_state['greenhouse_design']={'Structure':structure,'Crop':CROP_EN.get(crop,'Crop'),'Spans':spans,'Structures':structures,'Floor area (m²)':footprint,'Heating load (kW)':round(heating,2)}
 st.session_state['greenhouse_ep_inputs']={'floor_area_m2':footprint,'volume_m3':volume,'heating_setpoint_c':float(comfort),'cooling_setpoint_c':max(30.,float(comfort)+7),'u_value':U,'air_changes':air_changes}
 st.markdown('#### Cooling, Ventilation, Irrigation & Crop Lighting')
 st.caption('Preliminary engineering sizing. All assumptions are editable and reported with the outputs.')
 col_a,col_b,col_c=st.columns(3)
 with col_a:
  if design_climate:
   default_cooling=float(design_climate['observed_max'])
   st.caption('Outdoor cooling default: observed historical maximum (raw hourly data).')
  else:
   default_cooling=38.
   st.caption('Outdoor cooling default is a manual assumption until raw climate extremes are loaded.')
  outdoor_cooling=project_input('number_input','Outdoor summer design temperature (°C)',value=default_cooling)
  indoor_cooling=project_input('number_input','Indoor cooling setpoint (°C)',value=float(comfort)+5.,step=1.)
  solar_peak=project_input('number_input','Peak solar irradiance on roof (W/m²)',min_value=0.,max_value=1400.,value=750.,step=25.)
  cover_trans=st.slider('Cover solar transmittance',0.05,0.95,0.75,0.05)
 with col_b:
  shade=st.slider('Shading fraction',0.,0.95,0.25,0.05)
  allowed_rise=project_input('number_input','Ventilation design temperature difference (°C)',min_value=0.5,value=5.,step=0.5)
  max_ach=project_input('number_input','Installed ventilation capacity (air changes/hour)',min_value=0.,value=20.,step=1.)
  crop_coverage=st.slider('Crop-covered floor fraction',0.1,1.,0.85,0.05)
 with col_c:
  et0=project_input('number_input','Reference ET₀ (mm/day) — user assumption',min_value=0.,value=4.,step=0.5)
  irrigation_eff=st.slider('Irrigation application efficiency',0.3,1.,0.85,0.05)
  leaching=st.slider('Leaching fraction',0.,0.4,0.1,0.05)
  outdoor_dli=project_input('number_input','Outdoor daily light integral (mol/m²/day)',min_value=0.,value=25.,step=1.)
  lamp_eff=project_input('number_input','LED photon efficacy (µmol/J)',min_value=0.5,value=2.5,step=0.1)
  photoperiod=project_input('number_input','Lighting hours per day',min_value=1.,max_value=24.,value=14.)
 from greenhouse_design import design_greenhouse
 design=design_greenhouse(geometry=calculation,crop=CROP_EN.get(crop,'Unknown'),
   u_value=U,ach=air_changes,heating_setpoint=float(comfort),heating_outdoor=design_out,
   cooling_setpoint=indoor_cooling,cooling_outdoor=outdoor_cooling,
   solar_irradiance_wm2=solar_peak,glazing_transmittance=cover_trans,
   shading_fraction=shade,crop_coverage=crop_coverage,
   ventilation_delta_t=allowed_rise,max_air_changes=max_ach,
   irrigation_et0_mm_day=et0,irrigation_efficiency=irrigation_eff,
   leaching_fraction=leaching,par_dli_outdoor=outdoor_dli,
   lamp_efficacy=lamp_eff,photoperiod_h=photoperiod)
 st.session_state['greenhouse_design'].update({
   'Cooling sensible load (kW)':round(design['cooling_sensible_kw'],2),
   'Installed ventilation (m³/h)':round(design['ventilation_available_m3h'],1),
   'Gross irrigation (m³/day)':round(design['gross_irrigation_m3_day'],2),
   'Supplemental lighting (kWh/day)':round(design['supplemental_lighting_kwh_day'],2)})
 st.session_state['greenhouse_cooling_kw']=design['cooling_sensible_kw']
 st.session_state['greenhouse_water_m3_day']=design['gross_irrigation_m3_day']
 st.session_state['greenhouse_lighting_kwh_day']=design['supplemental_lighting_kwh_day']
 st.session_state['greenhouse_ventilation_m3h']=design['ventilation_available_m3h']
 st.markdown('#### Ventilation assessment')
 if design['ventilation_required_m3h'] is None:
  st.warning('Outdoor air is not cooler than the indoor cooling setpoint. Ventilation alone cannot achieve the setpoint; mechanical/evaporative cooling must be evaluated.')
 else:
  st.metric('Estimated required ventilation (m³/h)',f"{design['ventilation_required_m3h']:,.0f}")
  if design['ventilation_sufficient']:
   st.success('Installed ventilation meets this simplified sensible solar-heat removal estimate.')
  else:
   st.warning('Installed ventilation is below the estimated requirement; assess fans, vents and active cooling.')
 st.caption('The cooling value is a peak sensible-load screening result, NOT chiller capacity. Crop transpiration, humidity, evaporative-pad performance and equipment diversity are not included.')
 st.markdown('#### Crop lighting assessment')
 l1,l2,l3=st.columns(3)
 l1.metric('Crop target DLI minimum (mol/m²/day)',f"{design['dli_target_min_mol_m2_day']:.1f}")
 l2.metric('Estimated natural DLI (mol/m²/day)',f"{design['natural_dli_mol_m2_day']:.1f}")
 l3.metric('Supplemental lighting (kW)',f"{design['supplemental_lighting_kw']:.1f}")
 st.caption('DLI crop ranges and crop coefficient Kc are indicative screening assumptions. Enter measured outdoor DLI and locally validated ET₀ for meaningful site estimates.')
 st.markdown('#### Integrated Greenhouse Results')
 a,b,c,d,e=st.columns(5)
 a.metric('Heating (kW)',f"{heating:,.1f}")
 b.metric('Cooling sensible (kW)',f"{design['cooling_sensible_kw']:,.1f}")
 c.metric('Ventilation (m³/h)',f"{design['ventilation_available_m3h']:,.0f}")
 d.metric('Irrigation (m³/day)',f"{design['gross_irrigation_m3_day']:,.2f}")
 e.metric('Supplemental light (kWh/day)',f"{design['supplemental_lighting_kwh_day']:,.1f}")
 st.markdown('#### Geometry & Design Specifications')
 st.dataframe(pd.DataFrame([{'Structure':structure,'Crop':CROP_EN.get(crop,'Crop'),
   'Spans':spans,'Structures':structures,'Floor area (m²)':round(footprint,2),
   'Roof area (m²)':round(calculation['roof_area_m2'],2),
   'Envelope area (m²)':round(calculation['envelope_m2'],2),
   'Internal volume (m³)':round(volume,2),'Cover U (W/m²K)':U,
   'Infiltration (ACH)':air_changes,
   'Heating conduction (kW)':round(q_cond,2),
   'Heating infiltration (kW)':round(q_vent,2)}]),hide_index=True,use_container_width=True)
 st.warning('Geometry A/B/C and crop loads are preliminary; validate geometry, humidity, latent heat and wind/snow structure before procurement.')
 st.markdown('#### Integrated Greenhouse Design Report')
 report={**st.session_state['greenhouse_design'],**design,
    'Heating outdoor design temperature (°C)':design_out,
    'Cooling outdoor design temperature (°C)':outdoor_cooling,
    'Heating indoor setpoint (°C)':float(comfort),
    'Cooling indoor setpoint (°C)':indoor_cooling,
    'Solar irradiance assumption (W/m²)':solar_peak,
    'Cover solar transmittance':cover_trans,
    'Shading fraction':shade,
    'Reference ET0 (mm/day)':et0,
    'Irrigation efficiency':irrigation_eff,
    'Outdoor DLI (mol/m²/day)':outdoor_dli,
    'Crop':CROP_EN.get(crop,'Unknown'),
    'Climate data':('Synthetic demonstration' if st.session_state.get('demo_mode') else
       ('Historical extremes' if design_climate else 'Manual assumptions')),
    'Model status':'Preliminary screening; not validated; not an EnergyPlus result'}
 report_frame=pd.DataFrame([{'Parameter':str(k),'Value':str(v) if v is None else v} for k,v in report.items()])
 st.dataframe(report_frame,use_container_width=True,hide_index=True)
 st.download_button('Download Greenhouse Results (CSV)',
     report_frame.to_csv(index=False).encode('utf-8-sig'),
     file_name='RYAN_ENERGY_Greenhouse_Results.csv',mime='text/csv')
 import html
 rows=''.join('<tr><td>'+html.escape(str(k))+'</td><td>'+html.escape(str(v))+'</td></tr>' for k,v in report.items())
 html_report=('<!doctype html><html lang="en"><meta charset="utf-8"><title>RYAN ENERGY Greenhouse Design</title>'
  '<style>body{font:15px Segoe UI,Arial;margin:40px;color:#16354d;max-width:1000px}'
  'h1{border-bottom:3px solid #087eac;padding-bottom:12px}table{border-collapse:collapse;width:100%}'
  'td{border-bottom:1px solid #dce5ed;padding:9px}tr:nth-child(even){background:#f1f6fa}'
  '.warn{background:#fff3da;padding:15px;border-radius:8px}</style>'
  '<h1>RYAN ENERGY | Greenhouse Design Report</h1>'
  '<p class="warn">PRELIMINARY ENGINEERING SCREENING — NOT VALIDATED. Not an EnergyPlus simulation. '
  'Do not use for construction or equipment procurement without detailed engineering.</p>'
  '<table>'+rows+'</table>'
  '<h2>Method and limitations</h2>'
  '<p>Heating: envelope UAΔT and infiltration sensible load. Cooling: transmitted peak solar plus '
  'envelope and infiltration sensible gains. Ventilation: sensible heat removal if outdoor air is cooler. '
  'Irrigation: ET0 × indicative crop coefficient, corrected for application efficiency and leaching. '
  'Lighting: indicative crop DLI shortfall and LED photon efficacy.</p>'
  '<p>Humidity, evapotranspiration feedback, wind/snow structure, dynamic thermal mass and full hourly '
  'crop water balance are not simulated.</p></html>')
 st.download_button('Download Greenhouse Design Report (HTML)',html_report.encode('utf-8'),
    file_name='RYAN_ENERGY_Greenhouse_Report.html',mime='text/html')


if page=='Engine Connections':
 st.subheader('External Simulation Engines')
 st.caption('pvlib / PyPSA operate inside the app. EnergyPlus / WaterTAP require external engine installation and successful model runs. Detection alone is not validation.')
 ep_path=project_input('text_input','EnergyPlus executable path (energyplus.exe)',value=st.session_state.get('energyplus_path',''),placeholder=r'C:\EnergyPlusV25-1-0\energyplus.exe')
 st.session_state['energyplus_path']=ep_path
 statuses=engine_status(ep_path)
 for label in ('pvlib','PyPSA','EnergyPlus','WaterTAP'):
  st.write(('🟢' if statuses[label] else '⚪')+'  **'+label+'** — '+('Detected' if statuses[label] else 'Not detected'))
 st.divider()
 st.markdown('#### EnergyPlus — Native Model Run')
 st.caption('Runs a prepared IDF model against an EPW file. The Greenhouse screen can generate an equivalent-zone IDF automatically. Here you can also run your own prepared IDF.')
 idf=st.file_uploader('EnergyPlus model (.idf)',type=['idf'],key='ep_idf')
 epw=st.file_uploader('Weather (.epw)',type=['epw'],key='ep_epw')
 if st.button('Run EnergyPlus model',disabled=not(statuses['EnergyPlus'] and idf and epw)):
  try:
   with st.spinner('EnergyPlus running...'):
    ep_result=run_energyplus(idf.getvalue(),epw.getvalue(),statuses['EnergyPlus executable'])
   st.success(ep_result['status'])
   st.text_area('EnergyPlus error/warning report',ep_result['log'],height=180)
   if ep_result['csv_bytes']:
    st.download_button('Download EnergyPlus results CSV',ep_result['csv_bytes'],file_name='energyplus_results.csv')
  except Exception as exc:st.error(str(exc))
 st.divider()
 st.markdown('#### WaterTAP — Flowsheet Execution')
 wt=watertap_diagnostic()
 st.caption(wt['message'])
 st.warning('The Desalination page can generate a native WaterTAP RO flowsheet. This panel remains for trusted custom scripts. Execute only trusted scripts.')
 wt_file=st.file_uploader('Trusted WaterTAP flowsheet (.py)',type=['py'],key='wt_script')
 if st.button('Run WaterTAP flowsheet',disabled=not(wt['installed'] and wt_file)):
  try:
   with st.spinner('WaterTAP solving...'):
    output=run_watertap_script(wt_file.getvalue())
   st.success('WaterTAP script completed')
   st.code(output)
  except Exception as exc:st.error(str(exc))
 st.caption('EnergyPlus and WaterTAP are optional external installations, not bundled. Native models require compatible versions and working solvers.')

if page=='Model Checks':
 st.subheader('Model Checks · Engineering Diagnostics')
 st.caption('These are automatic verification checks, NOT comparisons with measured data and NOT standards certification.')
 result_check=st.session_state.get('dispatch') if st.session_state.get('dispatch_location')==(lat,lon,year) else None
 if result_check is None:st.info('Run an energy simulation first to check hourly balance and storage limits.')
 else:
  checks=validate_energy_balance(result_check)
  a,b,c=st.columns(3)
  a.metric('Maximum balance residual (kW)',f"{checks['max_abs_kw']:.6g}")
  b.metric('Hours exceeding 0.001 kW',str(checks['hours_outside_tolerance']))
  c.metric('Nonnegative grid imports', 'PASS' if checks['grid_nonnegative'] else 'FAIL')
  st.json(checks)
  if st.session_state.get('demo_mode'):st.warning('Synthetic demonstration inputs are not evidence of model accuracy.')
 if st.session_state.get('desal_design'):
  st.subheader('Desalination Water Balance')
  st.json(verify_desalination_balance(st.session_state['desal_design'],st.session_state['water_m3']))
 st.markdown('#### Engine Availability')
 st.json({k:v for k,v in engine_status(st.session_state.get('energyplus_path','')).items() if k!='EnergyPlus executable'})
 st.info('Validation against reference data and external standards will be completed after the engineering models are finalized.')

if page=='Model Documentation':
 st.subheader('Models, Sources & Limitations')
 st.markdown('''**Energy dispatch:** Hourly energy balance optimized internally, fixed generation capacities, battery dispatch and grid backup.\n\n**Solar:** pvlib solar position, measured/reanalysis GHI/DNI/DHI, isotropic transposition, Faiman cell temperature, temperature-adjusted module output and user losses.\n\n**Wind:** wind speed shear power law, manufacturer power curve if provided, otherwise approximate cubic power curve; site-specific wake and terrain modeling is not included.\n\n**Location:** GeoNamesCache hierarchical city listing (administrative codes), Open-Meteo historical hourly climate data.\n\n**Desalination:** RO uses feed/permeate/brine balance, idealized NaCl osmotic pressure, membrane permeability and hydraulic energy; MED/MSF use steam economy and simplified thermal intensity. All remain preliminary.\n\n**Greenhouse:** crop comfort temperatures and covering coefficients from supplied GREEN HOUSE.xlsx; geometry and structural loads not yet validated.\n\n**Scenario definition:** budget-based, land-based, equipment-count-based. These are independent design constraints, not three technology performance tiers.\n\n**Limitations:** preliminary engineering screening; not bankable yield assessment, site certification, electrical design or structural safety analysis. Costs and land-use coefficients are user assumptions.\n\n**References:** [PyPSA](https://docs.pypsa.org/) · [pvlib](https://pvlib-python.readthedocs.io/) · [Open-Meteo](https://open-meteo.com/) · [GeoNames](https://www.geonames.org/).''')

