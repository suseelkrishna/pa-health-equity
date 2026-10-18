"""Local county dashboard: presentation only, using validated release files."""

from pathlib import Path
import json
import pandas  # Initialize before interactive reruns use Plotly array validation.

import streamlit as st

from pa_public.presentation import METRICS, county_map, county_table
from pa_public.release import RELEASE_DIRECTORY, ReleaseError, load_release


st.set_page_config(page_title="Pennsylvania county health context", layout="wide")
st.html("""<style>
[data-testid='stMainBlockContainer'] {padding-top: 2.5rem; padding-bottom: 2rem;}
@media (max-width: 640px) {
  [data-testid='stLayoutWrapper']:has(> .st-key-county_map_frame) {flex: 0 0 300px !important; height: 300px !important;}
  .st-key-county_map_frame {height: 300px !important; min-height: 0 !important;}
}
</style>""")
st.title("Pennsylvania, county by county")
st.write("Explore social vulnerability and hospital presence across Pennsylvania's 67 counties. Choose a measure on the map, then view both measures for a county.")
st.caption("Sources: CDC/ATSDR SVI 2022 (2018–2022 ACS) · CMS February 25, 2026")
st.info("CDC/ATSDR source data is freely available from the [agency website](https://svi.cdc.gov/). This independently developed project is not endorsed by CDC, ATSDR, HHS, or the U.S. Government.")
with st.expander("Research note: this dashboard and the original study"):
    st.write("This dashboard explores two measures from the broader Pennsylvania health-equity study. The paper's Priority Opportunity Score (POS) findings are historical research and are not reproduced by these two separate measures.")

try:
    rows, geometry = load_release(Path(__file__).resolve().parent)
except ReleaseError as exc:
    st.error("Dashboard release unavailable. " + str(exc))
    st.info("Restore the complete versioned public bundle. See the README; the dashboard does not rebuild source data.")
    st.stop()

paper_url = json.loads((Path(__file__).parent / RELEASE_DIRECTORY / "release.json").read_text()).get("research_paper_url")
if paper_url:
    st.markdown("[Read the research paper]({})".format(paper_url))
else:
    st.caption("Research paper link unavailable in this release.")

map_column, detail_column = st.columns([2, 1], gap="large")
with detail_column:
    selected = st.selectbox("Choose a county", [row["county_name"] for row in rows])
    county = next(row for row in rows if row["county_name"] == selected)
    st.subheader("{} County".format(selected))
    st.caption("FIPS {} · outlined on the map".format(county["county_fips"]))
    st.markdown("**Social Vulnerability · {:.1f}/100**".format(county["svi_score_0_100"]))
    st.write("SVI 2022 · Higher means greater vulnerability to hazardous events. Pennsylvania percentile × 100.")
    st.markdown("**Hospital Count · {}**".format(county["hospital_count"]))
    st.write("CMS February 25, 2026 · Listed facilities, including all hospital types in this snapshot. Zero means no matching listing.")
    st.caption("Counts show presence; they do not measure services, capacity, or travel distance.")

with map_column:
    metric = st.selectbox("Map metric", list(METRICS))
    st.caption(METRICS[metric]["definition"])
    with st.container(height=460, border=False, key="county_map_frame"):
        st.plotly_chart(county_map(rows, geometry, metric, county["county_fips"]), width="stretch", height="stretch", theme=None,
                        config={"displayModeBar": False, "scrollZoom": False})
    st.caption("Outlined: {} County · Hover for values. SVI uses a fixed 0–100 legend; hospitals use a separate count scale.".format(selected))

st.divider()
st.subheader("County table")
query = st.text_input("Search counties", placeholder="Type a county name")
filtered = [row for row in rows if query.strip().casefold() in row["county_name"].casefold()]
table = county_table(filtered)
st.caption("{} of 67 counties · Two separate measures; vulnerability and facility presence have different meanings.".format(len(filtered)))
if table:
    st.dataframe(table, hide_index=True, width="stretch", height=min(330, 36 * (len(table) + 1) + 3),
                 column_config={"Social Vulnerability": st.column_config.NumberColumn(format="%.1f")})
else:
    st.info("No county names match. Clear or change the search to show counties.")
st.caption("Scores are shown to one decimal place. The CSV download preserves full precision and source values.")
st.download_button("Download full-precision county data (CSV)",
                   data=(Path(__file__).parent / RELEASE_DIRECTORY / "county_inputs.csv").read_bytes(),
                   file_name="pa_county_inputs.csv", mime="text/csv")

with st.expander("Sources, definitions, and limitations"):
    st.markdown("""
- **Social Vulnerability — CDC/ATSDR SVI 2022.** Pennsylvania-relative county rankings from 2018–2022 ACS estimates. The percentile is multiplied by 100. [SVI documentation](https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/10/SVI2022Documentation.pdf).
- **Hospital Count — CMS, February 25, 2026.** All 188 Pennsylvania facility IDs in this snapshot: acute care (133), psychiatric (26), critical access (17), VA acute care (7), and children's (5). [CMS hospitals archive](https://data.cms.gov/provider-data/archived-data/hospitals).
- **Map — Census TIGER/Line 2025.** Pennsylvania counties, simplified for display, with longitude/latitude coordinates. [Census source](https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/).

The measures use different data years and definitions. County summaries can hide differences within counties. Hospital listings do not establish care access or service adequacy. There is no combined score, priority tier, or new result from the paper's POS model. Source: CDC/ATSDR, CMS, U.S. Census Bureau. Their inclusion does not imply government endorsement. Statistical map boundaries are not legal land descriptions.
""")
