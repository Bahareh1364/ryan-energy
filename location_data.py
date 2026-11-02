"""Hierarchical country/province/city labels backed by GeoNames data."""
import geonamescache
import requests
from unidecode import unidecode
from functools import lru_cache

@lru_cache(maxsize=1)
def _gc(): return geonamescache.GeonamesCache()
@lru_cache(maxsize=1)
def _cities(): return list(_gc().get_cities().values())

def countries():
    return sorted([(c['name'],code) for code,c in _gc().get_countries().items()])

@lru_cache(maxsize=1)
def _admin_names():
    # GeoNames administrative-code file. Keep a local fallback if network is unavailable.
    names={'IR.01':'West Azerbaijan'}
    try:
        r=requests.get('https://download.geonames.org/export/dump/admin1CodesASCII.txt',timeout=12)
        r.raise_for_status()
        for line in r.text.splitlines():
            parts=line.split('\t')
            if len(parts)>=2: names[parts[0]]=parts[1]
    except requests.RequestException: pass
    return names

def provinces(code):
    codes=sorted({c.get('admin1code','') for c in _cities() if c['countrycode']==code and c.get('admin1code')})
    names=_admin_names()
    return [(names.get(f'{code}.{p}',f'Province {p}'),p) for p in codes]

def cities(code,province):
    found=[c for c in _cities() if c['countrycode']==code and c.get('admin1code')==province]
    # Deduplicate identically named settlements; favor the most populated entry.
    result={}
    for c in sorted(found,key=lambda x:-int(x.get('population',0))):
        key=c['name'].strip().casefold()
        if key not in result:result[key]=c
    return sorted(result.values(),key=lambda c:c['name'].casefold())


def english_city(name):
    """ASCII romanization for UI labels, not an authoritative local-language spelling."""
    return unidecode(str(name)).strip()
