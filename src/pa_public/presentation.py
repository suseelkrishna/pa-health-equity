"""Display configuration for existing values; no research calculations."""

import plotly.graph_objects as go


METRICS = {
    "Social Vulnerability": {
        "field": "svi_score_0_100", "unit": "Percentile × 100",
        "colors": ["#f5edf7", "#75447f"],
        "definition": "CDC/ATSDR SVI 2022 · Social vulnerability to hazardous events, ranked within Pennsylvania. Higher means greater relative vulnerability.",
    },
    "Hospital Count": {
        "field": "hospital_count", "unit": "CMS facilities",
        "colors": ["#eef3fa", "#285b96"],
        "definition": "CMS · February 25, 2026 · Unique listed facility IDs by county. Includes acute care, psychiatric, critical access, VA, and children's facilities.",
    },
}


def county_map(rows, geometry, metric, selected_fips=None):
    spec = METRICS[metric]
    values = [row[spec["field"]] for row in rows]
    maximum = max(values) if metric == "Hospital Count" else 100
    figure = go.Figure(go.Choropleth(
        geojson=geometry, featureidkey="id", locations=[r["county_fips"] for r in rows], z=values,
        text=[r["county_name"] for r in rows], zmin=0, zmax=maximum,
        colorscale=spec["colors"], marker_line_color="#ffffff", marker_line_width=0.6,
        colorbar={"title": {"text": spec["unit"], "side": "top"}, "orientation": "h",
                  "len": 0.9, "thickness": 12, "y": -0.1, "yanchor": "top", "x": 0.5, "outlinewidth": 0},
        hovertemplate="<b>%{text} County</b><br>" + metric + ": %{z" + (":.0f" if metric == "Hospital Count" else ":.1f") + "}<extra></extra>",
    ))
    if selected_fips is not None:
        feature = next(f for f in geometry["features"] if f["id"] == selected_fips)
        figure.add_trace(go.Choropleth(
            geojson={"type": "FeatureCollection", "features": [feature]},
            featureidkey="id", locations=[selected_fips], z=[0],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker_line_color="#18332f", marker_line_width=2.5,
            showscale=False, hoverinfo="skip",
        ))
    # Explicit geographic bounds avoid the padding of automatic world-map fitting.
    # These are display bounds, not transformed or recalculated county measures.
    figure.update_geos(fitbounds=False, visible=False, projection_type="mercator",
                       center={"lon": -77.6, "lat": 41.15},
                       lonaxis_range=[-80.6, -74.6], lataxis_range=[39.65, 42.6],
                       projection_scale=1)
    figure.update_layout(autosize=True, margin={"l": 2, "r": 2, "t": 2, "b": 80},
                         paper_bgcolor="rgba(0,0,0,0)", font={"family": "sans-serif", "size": 13})
    return figure


def county_table(rows):
    """Display-only rounding; input rows and downloadable CSV bytes stay intact."""
    return [{"County": r["county_name"], "FIPS": r["county_fips"],
             "Social Vulnerability": round(r["svi_score_0_100"], 1),
             "Hospital Count": r["hospital_count"]} for r in rows]
