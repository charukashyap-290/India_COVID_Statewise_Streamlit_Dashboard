import os
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="India COVID-19 Statewise Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_URL = "https://raw.githubusercontent.com/imdevskp/covid-19-india-data/refs/heads/master/state_level_daily.csv"
DATA_FILE = "data/covid_india_statewise.csv"
SAMPLE_FILE = "data/covid_india_statewise_sample.csv"

# ---------- CSS ----------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {
    padding: 24px 28px; border-radius: 22px; margin-bottom: 18px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #312e81 100%);
    color: white; box-shadow: 0 10px 30px rgba(15,23,42,.18);
}
.hero h1 {margin:0; font-size: 34px;}
.hero p {margin:7px 0 0; opacity:.82;}
.kpi {
    padding: 18px 20px; border-radius: 18px; background: rgba(255,255,255,.06);
    border: 1px solid rgba(148,163,184,.18); box-shadow: 0 7px 24px rgba(15,23,42,.08);
}
.kpi .label {font-size:13px; opacity:.72;}
.kpi .value {font-size:27px; font-weight:750; margin-top:3px;}
.small-note {font-size:12px; color:#64748b;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(148,163,184,.15);}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        try:
            r = requests.get(DATA_URL, timeout=30)
            r.raise_for_status()
            with open(DATA_FILE, "wb") as f:
                f.write(r.content)
        except Exception:
            pass

    path = DATA_FILE if os.path.exists(DATA_FILE) else SAMPLE_FILE
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["Confirmed","Deceased","Recovered"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df = df.dropna(subset=["Date","State_Name"])
    df = df[df["State_Name"].str.lower().ne("total")]
    df = df[df["State_Name"].str.lower().ne("state unassigned")]
    df["Active"] = (df["Confirmed"] - df["Recovered"] - df["Deceased"]).clip(lower=0)
    df["Recovery Rate"] = np.where(df["Confirmed"]>0, df["Recovered"]/df["Confirmed"]*100, 0)
    df["Fatality Rate"] = np.where(df["Confirmed"]>0, df["Deceased"]/df["Confirmed"]*100, 0)
    return df.sort_values(["Date","State_Name"])

df = load_data()
using_sample = not os.path.exists(DATA_FILE)

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>🇮🇳 India COVID-19 Statewise Analytics</h1>
  <p>Interactive state-level trends, rankings, KPIs and comparative analysis</p>
</div>
""", unsafe_allow_html=True)

if using_sample:
    st.warning("Full dataset could not be downloaded automatically. The ZIP includes a real-data sample. Run the app with internet access to load the complete historical CSV.")
else:
    st.success("Full historical statewise dataset loaded successfully.")

# ---------- Sidebar ----------
st.sidebar.header("🎛️ Dashboard Controls")

dates = sorted(df["Date"].dropna().unique())
date = st.sidebar.select_slider("Select date", options=dates, value=dates[-1], format_func=lambda x: pd.Timestamp(x).strftime("%d %b %Y"))

states = sorted(df["State_Name"].unique())
selected_states = st.sidebar.multiselect(
    "Compare states",
    states,
    default=[s for s in ["Maharashtra","Kerala","Uttar Pradesh","Delhi"] if s in states]
)

metric = st.sidebar.selectbox("Ranking metric", ["Confirmed","Active","Recovered","Deceased","Recovery Rate","Fatality Rate"])
top_n = st.sidebar.slider("Top states", 5, 15, 10)

d = df[df["Date"] == pd.Timestamp(date)].copy()
if d.empty:
    d = df[df["Date"] == df["Date"].max()].copy()
    date = d["Date"].iloc[0]

# ---------- KPIs ----------
confirmed = int(d["Confirmed"].sum())
recovered = int(d["Recovered"].sum())
deceased = int(d["Deceased"].sum())
active = int(d["Active"].sum())
recovery = recovered/confirmed*100 if confirmed else 0
fatality = deceased/confirmed*100 if confirmed else 0

cols = st.columns(6)
kpis = [
    ("Confirmed", confirmed),
    ("Active", active),
    ("Recovered", recovered),
    ("Deceased", deceased),
    ("Recovery Rate", f"{recovery:.1f}%"),
    ("Fatality Rate", f"{fatality:.2f}%"),
]
for c,(label,val) in zip(cols,kpis):
    c.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{val:,}</div></div>', unsafe_allow_html=True)

st.markdown(f"<div class='small-note'>Snapshot: {pd.Timestamp(date).strftime('%d %B %Y')} • States/UTs shown: {len(d)}</div>", unsafe_allow_html=True)
st.write("")

# ---------- Map ----------
st.subheader("🗺️ Statewise Impact Map")

GEOJSON_URL = "https://raw.githubusercontent.com/geohacker/india/master/state/india_telengana.geojson"
try:
    geo = requests.get(GEOJSON_URL, timeout=15).json()
    # GeoJSON has state names in st_nm for this common file.
    feature_names = []
    for f in geo.get("features", []):
        props = f.get("properties", {})
        feature_names.append(props.get("st_nm") or props.get("NAME_1") or props.get("name"))
    name_col = "State_Name"
    map_df = d.copy()
    # Best-effort normalization for common historical spellings.
    norm = {
        "Odisha":"Odisha", "Orissa":"Odisha",
        "Uttarakhand":"Uttarakhand", "Uttaranchal":"Uttarakhand",
        "Telangana":"Telangana", "Andhra Pradesh":"Andhra Pradesh",
        "Jammu and Kashmir":"Jammu & Kashmir",
    }
    map_df["MapState"] = map_df["State_Name"].replace(norm)
    fig_map = px.choropleth(
        map_df,
        geojson=geo,
        locations="MapState",
        featureidkey="properties.st_nm",
        color=metric,
        hover_name="State_Name",
        hover_data={"Confirmed":":,", "Active":":,", "Recovered":":,", "Deceased":":,", "Recovery Rate":":.1f", "Fatality Rate":":.2f", "MapState":False},
        color_continuous_scale="Turbo",
        title=f"{metric} by State/UT"
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(height=520, margin=dict(l=0,r=0,t=55,b=0))
    st.plotly_chart(fig_map, use_container_width=True)
except Exception:
    st.info("Map boundary file could not be loaded. The ranking chart below still works fully.")

# ---------- Rankings ----------
left, right = st.columns([1.05, 1])
with left:
    st.subheader(f"🏆 Top {top_n} States — {metric}")
    rank = d.sort_values(metric, ascending=False).head(top_n).sort_values(metric)
    fig = px.bar(rank, x=metric, y="State_Name", orientation="h", text=metric,
                 labels={"State_Name":"","value":metric}, template="plotly_white")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(height=430, margin=dict(l=0,r=35,t=10,b=0))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📊 Active vs Recovered vs Deceased")
    stack = d.nlargest(10, "Confirmed").copy()
    fig2 = go.Figure()
    for col in ["Active","Recovered","Deceased"]:
        fig2.add_trace(go.Bar(name=col, x=stack["State_Name"], y=stack[col]))
    fig2.update_layout(barmode="stack", template="plotly_white", height=430,
                       xaxis_title="", yaxis_title="Cases",
                       margin=dict(l=0,r=0,t=10,b=70), legend=dict(orientation="h"))
    st.plotly_chart(fig2, use_container_width=True)

# ---------- National trend ----------
st.subheader("📈 India-wide Trend")
trend = df.groupby("Date", as_index=False)[["Confirmed","Recovered","Deceased","Active"]].sum()
fig3 = go.Figure()
for col in ["Confirmed","Active","Recovered","Deceased"]:
    fig3.add_trace(go.Scatter(x=trend["Date"], y=trend[col], mode="lines", name=col))
fig3.update_layout(template="plotly_white", height=470, hovermode="x unified",
                   yaxis_title="Cases", xaxis_title="")
st.plotly_chart(fig3, use_container_width=True)

# ---------- State comparison ----------
st.subheader("🔎 State Comparison")
if selected_states:
    comp = df[df["State_Name"].isin(selected_states)].copy()
    fig4 = px.line(comp, x="Date", y="Confirmed", color="State_Name",
                   markers=False, template="plotly_white",
                   labels={"Confirmed":"Confirmed Cases","Date":"","State_Name":"State"})
    fig4.update_layout(height=430, hovermode="x unified")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Select at least one state from the sidebar.")

# ---------- Rates ----------
c1, c2 = st.columns(2)
with c1:
    st.subheader("💚 Recovery Rate by State")
    rr = d.sort_values("Recovery Rate", ascending=False).head(10).sort_values("Recovery Rate")
    fig5 = px.bar(rr, x="Recovery Rate", y="State_Name", orientation="h",
                  text="Recovery Rate", template="plotly_white")
    fig5.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig5.update_layout(height=400, xaxis_title="Recovery Rate (%)", yaxis_title="")
    st.plotly_chart(fig5, use_container_width=True)

with c2:
    st.subheader("⚠️ Fatality Rate by State")
    fr = d.sort_values("Fatality Rate", ascending=False).head(10).sort_values("Fatality Rate")
    fig6 = px.bar(fr, x="Fatality Rate", y="State_Name", orientation="h",
                  text="Fatality Rate", template="plotly_white")
    fig6.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig6.update_layout(height=400, xaxis_title="Fatality Rate (%)", yaxis_title="")
    st.plotly_chart(fig6, use_container_width=True)

# ---------- Data table ----------
st.subheader("📋 Statewise Snapshot")
show = d[["State_Name","Confirmed","Active","Recovered","Deceased","Recovery Rate","Fatality Rate"]].copy()
show["Recovery Rate"] = show["Recovery Rate"].round(2)
show["Fatality Rate"] = show["Fatality Rate"].round(2)
show = show.sort_values("Confirmed", ascending=False)
st.dataframe(show, use_container_width=True, hide_index=True)

csv = show.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Current Snapshot CSV", csv, "india_covid_statewise_snapshot.csv", "text/csv")

st.caption("Data visualization project for educational/portfolio use. COVID-19 figures are historical reported data and should not be interpreted as current medical guidance.")
