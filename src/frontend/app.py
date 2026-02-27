from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


API_BASE = os.getenv("FLOOD_API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Bengaluru Flood Vulnerability", layout="wide")
st.title("Bengaluru Flood Risk Decision Dashboard")
st.caption("Monthly city risk intelligence (2020-2024) for planning and response.")


def _get(path: str) -> dict:
    response = requests.get(f"{API_BASE}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


try:
    metadata = _get("/metadata")
    latest = _get("/vulnerability/latest?limit=5000")
    by_zone = _get("/vulnerability/by_zone?bins_lat=8&bins_lon=8")
    timeseries = _get("/vulnerability/timeseries")
except Exception as exc:
    st.error(f"Failed to connect to API at {API_BASE}: {exc}")
    st.stop()

st.subheader("Metadata")
st.json(
    {
        "rows": metadata.get("rows"),
        "months": [metadata.get("months", [None])[0], metadata.get("months", [None])[-1]],
        "rank_correlation_spearman": metadata.get("evaluation", {}).get("rank_correlation_spearman"),
        "temporal_r2": metadata.get("training_metrics", {}).get("temporal", {}).get("r2"),
    }
)

rows = latest.get("rows", [])
if not rows:
    st.warning("No latest vulnerability rows available.")
    st.stop()

df = pd.DataFrame(rows)
zone_df = pd.DataFrame(by_zone.get("rows", []))
series_df = pd.DataFrame(timeseries.get("rows", []))


def classify_city_risk(score: float) -> str:
    if score >= 0.70:
        return "Very High"
    if score >= 0.55:
        return "High"
    if score >= 0.40:
        return "Moderate"
    return "Low"


latest_avg = float(df["vulnerability_score"].mean())
latest_risk = classify_city_risk(latest_avg)
top20_cutoff = df["vulnerability_score"].quantile(0.8)
hotspot_tiles = int((df["vulnerability_score"] >= top20_cutoff).sum())
total_tiles = int(df.shape[0])
hotspot_share = 100.0 * hotspot_tiles / max(total_tiles, 1)

st.subheader("City Snapshot")
c1, c2, c3 = st.columns(3)
c1.metric("Current City Risk Level", latest_risk, help="Based on the latest month average risk score.")
c2.metric("Average Risk Score (Latest Month)", f"{latest_avg:.2f}")
c3.metric("Hotspot Coverage", f"{hotspot_share:.1f}%", help="Share of grid tiles in top 20% risk.")

if latest_risk in {"Very High", "High"}:
    st.warning(
        "Priority recommendation: pre-position pumps and emergency teams in top hotspot zones before heavy rainfall weeks."
    )
elif latest_risk == "Moderate":
    st.info("Watchlist recommendation: strengthen drainage cleaning and ward-level preparedness in hotspot pockets.")
else:
    st.success("Current city risk is comparatively low; continue monitoring and preventive maintenance.")

st.subheader(f"Risk Map (Latest Month: {latest.get('year_month')})")
st.caption("Each point is a city tile. Denser hotspot clusters indicate higher flood vulnerability concentration.")
st.map(df.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])

st.subheader("Top Priority Zones (Plain-Language List)")
if not zone_df.empty:
    zone_df = zone_df.sort_values("vulnerability_score", ascending=False).head(15)
    zone_df["priority_level"] = zone_df["vulnerability_score"].map(
        lambda x: "Immediate" if x >= 0.70 else ("High" if x >= 0.55 else "Medium")
    )
    st.dataframe(
        zone_df[["zone_id", "vulnerability_score", "priority_level"]].rename(
            columns={
                "zone_id": "Zone",
                "vulnerability_score": "Risk Score",
                "priority_level": "Priority",
            }
        ),
        use_container_width=True,
    )

st.subheader("Seasonal Risk Trend (City-Wide)")
if not series_df.empty:
    st.line_chart(series_df.set_index("year_month")[["vulnerability_score"]])

st.subheader("How to Use This Dashboard")
st.markdown(
    """
- **Immediate actions:** focus first on zones marked `Immediate` priority.
- **Resource planning:** allocate more crews and drainage resources where hotspot coverage is rising month-to-month.
- **Season preparedness:** use trend increase periods to trigger pre-monsoon ward-level action plans.
"""
)
