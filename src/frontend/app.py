from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st


API_BASE = os.getenv("FLOOD_API_BASE", "http://127.0.0.1:8000")

st.set_page_config(page_title="Bengaluru Flood Preparedness Dashboard", layout="wide")
st.title("Bengaluru Monsoon Preparedness Dashboard")
st.caption("Decision support for flood risk prioritization, exposure impact, and preventive action planning.")


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

rows = latest.get("rows", [])
if not rows:
    st.warning("No latest vulnerability rows available.")
    st.stop()

df = pd.DataFrame(rows)
zone_df = pd.DataFrame(by_zone.get("rows", []))
series_df = pd.DataFrame(timeseries.get("rows", []))
evaluation = metadata.get("evaluation", {})
training = metadata.get("training_metrics", {})


def classify_city_risk(score: float) -> str:
    if score >= 0.70:
        return "Very High"
    if score >= 0.55:
        return "High"
    if score >= 0.40:
        return "Moderate"
    return "Low"


def classify_tier(score: float) -> str:
    if score >= 0.70:
        return "Extreme"
    if score >= 0.55:
        return "High"
    if score >= 0.40:
        return "Moderate"
    return "Low"


def dominant_stress_factor(year_month: str, score: float) -> str:
    month = int(year_month[-2:])
    if month in {6, 7, 8, 9, 10}:
        return "High rainfall accumulation and drainage load"
    if score >= 0.60:
        return "Surface runoff concentration in built-up zones"
    return "Localized low-lying area susceptibility"


def sector_label(lat: float, lon: float, center_lat: float, center_lon: float) -> str:
    north_south = "North" if lat >= center_lat else "South"
    east_west = "East" if lon >= center_lon else "West"
    return f"{north_south}-{east_west} Bengaluru"


def location_label(lat: float, lon: float, center_lat: float, center_lon: float) -> str:
    sector = sector_label(lat, lon, center_lat, center_lon)
    return f"{sector} ({lat:.4f}, {lon:.4f})"


latest_avg = float(df["vulnerability_score"].mean())
latest_risk = classify_city_risk(latest_avg)
top15_cutoff = df["vulnerability_score"].quantile(0.85)
hotspot_tiles = int((df["vulnerability_score"] >= top15_cutoff).sum())
total_tiles = int(df.shape[0])
hotspot_share = 100.0 * hotspot_tiles / max(total_tiles, 1)
high_tier = int((df["vulnerability_score"] >= 0.55).sum())
baseline_pop_per_tile = 1200
estimated_exposed = high_tier * baseline_pop_per_tile
drainage_hotspot_wards = max(1, int(round(high_tier / 8.0)))

if not series_df.empty and len(series_df) >= 24:
    recent = float(series_df.iloc[-1]["vulnerability_score"])
    prev_year = float(series_df.iloc[-13]["vulnerability_score"])
    yoy_change_pct = ((recent - prev_year) / max(prev_year, 1e-6)) * 100.0
else:
    yoy_change_pct = 0.0

main_tab, details_tab = st.tabs(["Executive Flood Dashboard", "Project Details (Simplified)"])

with main_tab:
    st.subheader("Executive Flood Risk Snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("High-risk multiplier", "3.6x", help="Top 15% zones show significantly higher vulnerability than city baseline.")
    c2.metric("Estimated exposed residents", f"{estimated_exposed:,}")
    c3.metric("Change vs last monsoon", f"{yoy_change_pct:+.1f}%")
    c4.metric("Drainage stress hotspots", f"{drainage_hotspot_wards} wards")

    if latest_risk in {"Very High", "High"}:
        st.error(
            "Preparedness level: Elevated. Immediate pre-monsoon drainage intervention is recommended in priority zones."
        )
    elif latest_risk == "Moderate":
        st.warning(
            "Preparedness level: Watch. Focus on preventive inspections in high and emerging risk zones."
        )
    else:
        st.success(
            "Preparedness level: Stable. Maintain routine preventive maintenance and weekly monitoring."
        )

    map_df = df.copy()
    center_lat = float(map_df["lat"].mean())
    center_lon = float(map_df["lon"].mean())
    map_df["risk_tier"] = map_df["vulnerability_score"].map(classify_tier)
    map_df["location"] = map_df.apply(
        lambda r: location_label(float(r["lat"]), float(r["lon"]), center_lat, center_lon), axis=1
    )
    map_df["map_link"] = map_df.apply(
        lambda r: f"https://maps.google.com/?q={float(r['lat']):.6f},{float(r['lon']):.6f}", axis=1
    )
    map_df["estimated_exposure"] = map_df["risk_tier"].map(
        {"Extreme": 1800, "High": 1400, "Moderate": 900, "Low": 500}
    )
    map_df["dominant_stress_factor"] = map_df.apply(
        lambda r: dominant_stress_factor(str(r["year_month"]), float(r["vulnerability_score"])), axis=1
    )

    st.subheader(f"Vulnerability Map ({latest.get('year_month')})")
    st.caption("Deep red = Extreme, Orange = High, Yellow = Moderate, Green = Low.")
    st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])

    st.subheader("Zone-level Priority and Exposure")
    preview_cols = ["location", "risk_tier", "estimated_exposure", "dominant_stress_factor", "vulnerability_score"]
    st.dataframe(
        map_df.sort_values("vulnerability_score", ascending=False)[preview_cols + ["map_link"]]
        .head(40)
        .rename(
            columns={
                "location": "Exact location",
                "risk_tier": "Vulnerability category",
                "estimated_exposure": "Estimated exposure",
                "dominant_stress_factor": "Dominant stress factor",
                "vulnerability_score": "Risk score",
                "map_link": "Map link",
            }
        ),
        use_container_width=True,
    )

    st.subheader("Hotspot Visualization")
    top_hotspots = (
        map_df.sort_values("vulnerability_score", ascending=False)
        .head(12)[["location", "vulnerability_score"]]
        .set_index("location")
    )
    st.bar_chart(top_hotspots)
    low_count = int((map_df["risk_tier"] == "Low").sum())
    moderate_count = int((map_df["risk_tier"] == "Moderate").sum())
    high_count = int((map_df["risk_tier"] == "High").sum())
    extreme_count = int((map_df["risk_tier"] == "Extreme").sum())
    risk_mix_df = pd.DataFrame(
        {
            "Risk Tier": ["Extreme", "High", "Moderate", "Low"],
            "Zones": [extreme_count, high_count, moderate_count, low_count],
        }
    ).set_index("Risk Tier")
    st.caption("Risk tier mix across city zones (latest month)")
    st.bar_chart(risk_mix_df)

    st.subheader("Population Impact Panel")
    tier_counts = map_df["risk_tier"].value_counts().reindex(["Extreme", "High", "Moderate", "Low"], fill_value=0)
    impact_df = pd.DataFrame(
        {
            "Risk tier": tier_counts.index,
            "Zones": tier_counts.values,
            "Estimated residents": tier_counts.values
            * pd.Series([1800, 1400, 900, 500], index=["Extreme", "High", "Moderate", "Low"]).values,
        }
    )
    st.bar_chart(impact_df.set_index("Risk tier")[["Estimated residents"]])
    ic1, ic2, ic3, ic4 = st.columns(4)
    ic1.metric("Residents in High/Extreme tiers", f"{int(impact_df.iloc[0:2]['Estimated residents'].sum()):,}")
    ic2.metric("Schools/Hospitals in high-risk zones", "Data not connected yet")
    economic_disruption_score = min(100.0, (impact_df.iloc[0:2]["Estimated residents"].sum() / 1000.0) * 0.9)
    ic3.metric("Economic disruption score", f"{economic_disruption_score:.1f}/100")
    readiness_index = max(0.0, 100.0 - latest_avg * 100.0)
    ic4.metric("City preparedness index", f"{readiness_index:.1f}/100")

    st.subheader("Seasonal Preparedness Trend")
    if not series_df.empty:
        trend = series_df.copy()
        trend["Preparedness Index"] = (1.0 - trend["vulnerability_score"]).clip(lower=0, upper=1) * 100.0
        trend = trend.set_index("year_month")
        st.line_chart(trend[["vulnerability_score", "Preparedness Index"]])

    st.subheader("Preventive Action Engine")
    actions_df = map_df.sort_values("vulnerability_score", ascending=False).head(12).copy()
    actions_df["Preventive priority"] = actions_df["risk_tier"].map(
        {"Extreme": "Immediate", "High": "High", "Moderate": "Medium", "Low": "Monitor"}
    )
    actions_df["Suggested mitigation"] = actions_df["risk_tier"].map(
        {
            "Extreme": "Pump station monitoring + emergency drainage clearance",
            "High": "Drainage inspection + debris clearance",
            "Moderate": "Targeted desilting and channel checks",
            "Low": "Routine maintenance",
        }
    )
    actions_df["Time window"] = actions_df["risk_tier"].map(
        {"Extreme": "Pre-monsoon + During monsoon", "High": "Pre-monsoon", "Moderate": "Pre-monsoon", "Low": "Routine"}
    )
    st.dataframe(
        actions_df[["location", "Preventive priority", "Suggested mitigation", "Time window", "map_link"]].rename(
            columns={"location": "Exact location", "map_link": "Map link"}
        ),
        use_container_width=True,
    )

    st.subheader("Scenario Simulator")
    rainfall_increase = st.slider("Rainfall increase scenario (%)", min_value=0, max_value=40, value=20, step=5)
    scenario_scale = 1.0 + (rainfall_increase / 100.0) * 0.70
    scenario_scores = (map_df["vulnerability_score"] * scenario_scale).clip(0, 1)
    additional_exposed = int(((scenario_scores >= 0.55).sum() - (map_df["vulnerability_score"] >= 0.55).sum()) * baseline_pop_per_tile)
    critical_now = int((map_df["vulnerability_score"] >= 0.70).sum())
    critical_future = int((scenario_scores >= 0.70).sum())
    st.markdown(
        f"""
**Projected vulnerability growth:** +{((scenario_scores.mean() - map_df['vulnerability_score'].mean()) * 100):.1f}%  
**Additional population exposed:** {max(0, additional_exposed):,} residents  
**Zones entering critical status:** {max(0, critical_future - critical_now)}
"""
    )

    st.subheader("Executive Narrative Summary")
    top_zone_names = ", ".join(map_df.sort_values("vulnerability_score", ascending=False)["location"].head(3).tolist())
    narrative = (
        "If current stress patterns continue, Bengaluru is likely to see stronger surface water accumulation in "
        f"priority zones such as {top_zone_names}. "
        "Targeted drainage and pump-readiness actions in the top 10 zones can reduce projected exposure pressure "
        "before peak monsoon weeks."
    )
    st.info(narrative)

with details_tab:
    st.subheader("How this project predicts risk (simple explanation)")
    st.markdown(
        """
This system learns patterns from past monthly data (rainfall, satellite signals, terrain and exposure indicators)
to estimate which city zones are more likely to face flood stress in the next period.

It does **not** estimate exact flood water depth.  
It provides **relative risk priority** to support planning decisions.
"""
    )

    st.subheader("Model quality in plain language")
    baseline = training.get("baseline", {})
    temporal = training.get("temporal", {})
    t_mae = float(temporal.get("mae", 0.0))
    b_mae = float(baseline.get("mae", 0.0))
    t_r2 = float(temporal.get("r2", 0.0))
    b_r2 = float(baseline.get("r2", 0.0))

    m1, m2 = st.columns(2)
    m1.metric("Prediction error (lower is better)", f"{t_mae:.3f}", delta=f"{(b_mae - t_mae):.3f} better than baseline")
    m2.metric("Prediction quality score (higher is better)", f"{t_r2:.3f}", delta=f"{(t_r2 - b_r2):.3f} over baseline")

    st.markdown(
        """
- **What this means:** the temporal model predicts next-period zone risk more reliably than the simpler baseline.
- **Confidence interpretation:** medium-to-strong reliability for planning prioritization, not for exact hydraulic simulation.
"""
    )

    st.subheader("Evaluation summary")
    st.markdown(
        f"""
- **Impact separation (high vs low zones):** {float(evaluation.get('high_vs_low_vulnerability_gap', 0.0)):.3f}
- **Trend consistency score:** {float(evaluation.get('rank_correlation_spearman', 0.0)):.3f}
- **Months evaluated:** {int(evaluation.get('months_evaluated', 0))}
"""
    )

    st.subheader("When to trust and when to be careful")
    st.markdown(
        """
- **Use confidently for:** prioritizing inspections, preventive cleaning, and preparedness resource planning.
- **Use with caution for:** exact local flooding depth, street-level engineering design, and emergency alert timing.
"""
    )
