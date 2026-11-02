"""Preliminary desalination balances. Not a membrane vendor or WaterTAP model."""

def estimate_desalination(tech, product_m3_day, tds_mg_l, recovery, temperature_c, pump_eff, erd_eff,
                          permeability=1.5,fouling=0.15,permeate_tds=300,effects=8,gor=8):
    if not (0<recovery<1 and 0<pump_eff<=1 and 0<=erd_eff<1):raise ValueError('Invalid efficiencies or recovery')
    if min(product_m3_day,tds_mg_l,temperature_c)<0:raise ValueError('Negative input')
    feed=product_m3_day/recovery
    brine=feed-product_m3_day
    brine_tds=(feed*tds_mg_l-product_m3_day*permeate_tds)/brine if brine>0 else 0
    if brine_tds<0:raise ValueError('Permeate TDS and recovery violate salt mass balance')
    if tech=='RO':
        # van't Hoff NaCl-equivalent approximation, mol/L, R in L.bar/mol/K
        temp_k=temperature_c+273.15
        def osm(s):return 2*(s/1000/58.44)*0.08314*temp_k
        feed_osm=osm(tds_mg_l);brine_osm=osm(brine_tds);perm_osm=osm(permeate_tds)
        delta_osm=(feed_osm+brine_osm)/2-perm_osm
        net_pressure=12.0 if tds_mg_l>=10000 else 5.0 # explicit screening design flux pressure
        pressure=max(5.,delta_osm+net_pressure)
        flux=max(0.1,permeability*(pressure-delta_osm)*(1-fouling)) # L/m2/h
        membrane_area=product_m3_day*1000/(24*flux) if flux else 0
        feed_pump=pressure*feed*0.02777778/pump_eff
        brine_recovery=pressure*brine*0.02777778*erd_eff
        auxiliary=0.5*product_m3_day
        elec=max(0,feed_pump-brine_recovery)+auxiliary
        return dict(electric_sec=elec/product_m3_day if product_m3_day else 0,electric_day=elec,
            thermal_day=0.,feed_m3_day=feed,brine_m3_day=brine,brine_tds_mg_l=brine_tds,
            design_pressure_bar=pressure,membrane_area_m2=membrane_area,
            osmotic_pressure_bar=delta_osm,permeate_flux_lmh=flux,
            note='RO screening model: NaCl-equivalent osmotic pressure, assumed net pressure and flux, simplified ERD. NOT WaterTAP; vendor membrane design and pretreatment still required.')
    # Heat is computed from assumed latent heat and specified GOR (steam economy).
    # GOR is an input, NOT predicted from number of effects or feed salinity.
    if gor<=0:raise ValueError('GOR must be positive')
    latent_kj_kg=2300. # screening latent heat of heating steam
    thermal=product_m3_day*1000*latent_kj_kg/(gor*3600)
    # electrical auxiliaries are user-independent scenario constants, not process simulation
    elec_sec=2.0 if tech=='MED' else 4.0
    elec=product_m3_day*elec_sec
    return dict(electric_sec=elec_sec,electric_day=elec,thermal_day=thermal,
        thermal_sec=thermal/product_m3_day if product_m3_day else 0,feed_m3_day=feed,
        brine_m3_day=brine,brine_tds_mg_l=brine_tds,design_pressure_bar=None,
        assumed_gor=gor,number_of_effects=effects,
        note=f'{tech} screening: steam heat from assumed GOR={gor:g} and 2300 kJ/kg latent heat; electric auxiliary intensity is assumed. This is NOT a thermal flowsheet model.')
