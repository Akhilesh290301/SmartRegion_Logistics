# SmartRegion Logistics Partner Matching

Bilingual Streamlit prototype connected directly to the Eclipse BaSyx AAS Environment.

## Run on macOS

Keep Docker Desktop and your BaSyx containers running.

```bash
cd ~/Documents/SmartRegion_BaSyx
docker compose ps
```



```bash
cd SmartRegion_Streamlit_App
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open:

`http://localhost:8501`

Default BaSyx endpoint:

`http://localhost:8081`

Optional override:

```bash
export BASYX_BASE_URL=http://localhost:8081
streamlit run app.py
```

## Matching

Mandatory checks:
- active service
- capability
- operational resource
- capacity and unit
- time-window availability
- temperature range where required
- service-distance limit when supplied
- maximum price when supplied

Compatible candidates are ranked using normalized user-selected weights for price, distance/service-range utilization and availability.

The top-right DE toggle switches the UI, statuses, controlled vocabulary labels and explanations between English and German.
