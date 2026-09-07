# 🇮🇳 India COVID-19 Statewise Analytics Dashboard

A polished Streamlit + Plotly data-visualization project for analyzing COVID-19
reported cases across Indian states/UTs.

## Main features
- KPI cards: Confirmed, Recovered, Deceased, Active
- Interactive date slider
- State selector
- Statewise choropleth map (loaded from a public GeoJSON)
- Top states ranking
- Confirmed / Recovered / Death trend
- Active cases trend
- Recovery Rate and Fatality Rate
- State comparison
- Download filtered CSV
- Automatic download of the full historical dataset
- Offline fallback sample dataset included in `data/`

## Data source
Primary dataset:
`https://github.com/imdevskp/covid-19-india-data/blob/master/state_level_daily.csv`

Raw CSV:
`https://raw.githubusercontent.com/imdevskp/covid-19-india-data/refs/heads/master/state_level_daily.csv`

The dataset contains Date, State code, Confirmed, Deceased, Recovered and State_Name.
The repository describes it as state-level daily COVID-19 data.

Alternative official community archive:
`https://data.covid19india.org/`
Its documentation provides a statewise time-series CSV and other India COVID datasets.

## Run
1. Open PowerShell in this folder.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Run:
   `python -m streamlit run app.py`

The app first tries to download the complete CSV automatically. If internet is
unavailable, it uses the included sample CSV.

## Portfolio title
"India COVID-19 Statewise Analytics Dashboard"

## Suggested resume bullets
- Built an interactive Streamlit dashboard to analyze COVID-19 trends across Indian states/UTs.
- Performed data cleaning, KPI calculation, trend analysis, state ranking and rate analysis.
- Created interactive Plotly visualizations including statewise maps, trend charts and comparison views.
