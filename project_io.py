"""Portable, versioned RYAN ENERGY project data. No pickle/code execution."""
import json
import math
from datetime import datetime, timezone

FORMAT = 'RYAN_ENERGY_PROJECT'
VERSION = 1
SKIP_KEYS = {
    'dispatch', 'dispatch_location', 'weather', 'weather_key', 'design_climate',
    'design_climate_key', 'run_requested', 'economics_summary', 'watertap_result',
    'energyplus_result', 'curve', '_project_upload', '_project_loaded_message',
    '_project_ui', 'active_page', 'expanded_menus', 'demo_mode'
}

def _clean(value, depth=0):
    if depth > 12:
        raise ValueError('Nested project data too deep')
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('Non-finite value in project')
        return value
    if isinstance(value, dict):
        return {str(k): _clean(v, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v, depth + 1) for v in value]
    # numpy scalar support, not arbitrary Python objects
    if type(value).__module__.startswith('numpy') and hasattr(value, 'item'):
        return _clean(value.item(), depth + 1)
    raise TypeError('Unsupported project value: ' + type(value).__name__)

def export_project(session):
    state = {}
    for key, val in session.items():
        if key.startswith('_') or key in SKIP_KEYS or key.startswith(('nav_', 'group_')):
            continue
        try:
            state[key] = _clean(val)
        except (TypeError, ValueError):
            # Optional uploaded manufacturer curves are not portable JSON.
            if key in ('wind_settings', 'pv_settings') and isinstance(val, dict):
                state[key] = _clean({k:v for k,v in val.items() if k != 'curve'})
            continue
    ui = _clean(session.get('_project_ui', {}))
    doc = {'format': FORMAT, 'version': VERSION,
           'saved_at_utc': datetime.now(timezone.utc).isoformat(),
           'state': state, 'ui': ui}
    return json.dumps(doc, ensure_ascii=False, indent=2).encode('utf-8')

def import_project(blob):
    if len(blob) > 2_000_000:
        raise ValueError('Project JSON exceeds 2 MB')
    doc = json.loads(blob.decode('utf-8-sig'))
    if not isinstance(doc, dict) or doc.get('format') != FORMAT or doc.get('version') != VERSION:
        raise ValueError('Not a supported RYAN ENERGY project file')
    state, ui = doc.get('state'), doc.get('ui')
    if not isinstance(state, dict) or not isinstance(ui, dict):
        raise ValueError('Invalid project structure')
    if any(not isinstance(k, str) for k in state):
        raise ValueError('Invalid state key')
    state = {k:v for k,v in state.items() if not k.startswith('_') and k not in SKIP_KEYS}
    return _clean(state), _clean(ui)
