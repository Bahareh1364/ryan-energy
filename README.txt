RYAN ENERGY v11 — Local review edition + server-ready API foundation

IMPORTANT: No VPS or public domain is needed for an in-person demo.
Windows local launch: double-click START_RYAN_ENERGY.bat in the extracted folder.
Or open CMD in this folder and run:
 C:\Users\Notebook\.venv\Scripts\python.exe -m pip install -r requirements.txt
 C:\Users\Notebook\.venv\Scripts\python.exe -m streamlit run app.py

Offline mode: open Climate dataset -> Load Offline Demonstration Climate.
Synthetic climate is for interface demos ONLY, never model validation or design.
Configure solar/wind in their pages, then run Simulation.
Model Checks shows numerical consistency checks, not standards certification.

Server migration: optional FastAPI foundation in api_server.py.
 python -m pip install -r requirements_server.txt
 uvicorn api_server:app --host 127.0.0.1 --port 8000
 GET /health, POST /v1/greenhouse/screening, POST /v1/desalination/ro-screening
Do NOT expose this development server publicly without authentication,
rate limiting, HTTPS, job queue, input validation review and isolation.

EnginePlus and WaterTAP are NOT bundled and native execution still requires
compatible installations. Native EnergyPlus greenhouse is an equivalent
thermal zone, not a calibrated full greenhouse. WaterTAP solver must converge.

Formal review documentation and measured-data validation remain pending.
