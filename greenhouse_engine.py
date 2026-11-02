"""Transparent greenhouse geometry and peak sensible heating screening model."""
import math

def greenhouse_heating(shape,width,length,wall_height,rise,spans,buildings,u,ach,inside,outside):
    if min(width,length,wall_height,rise,spans,buildings)<=0:raise ValueError('All geometry must be positive')
    width_total=width*spans
    floor=width_total*length*buildings
    if shape=='A':
        roof_per_span=2*math.hypot(width/2,rise)
        gable_end=width*rise/2
        extra_volume=width*rise/2
    elif shape=='B':
        # circular arc through chord width with sagitta rise
        radius=width**2/(8*rise)+rise/2
        angle=2*math.asin(min(1,width/(2*radius)))
        roof_per_span=radius*angle
        gable_end=radius**2/2*(angle-math.sin(angle))
        extra_volume=gable_end
    else:
        # C: semicircular connected arches; rise is derived from span width.
        radius=width/2
        roof_per_span=math.pi*radius
        gable_end=math.pi*radius**2/2
        extra_volume=gable_end
    roof=roof_per_span*length*spans*buildings
    sides=2*length*wall_height*buildings
    endwalls=2*(width_total*wall_height+gable_end*spans)*buildings
    envelope=roof+sides+endwalls
    volume=(width_total*length*wall_height+extra_volume*length*spans)*buildings
    dt=max(0,inside-outside)
    transmission=u*envelope*dt/1000
    infiltration=0.33*ach*volume*dt/1000
    return {'floor_area_m2':floor,'roof_area_m2':roof,'envelope_m2':envelope,
            'volume_m3':volume,'transmission_kw':transmission,'infiltration_kw':infiltration,
            'heating_kw':transmission+infiltration}
