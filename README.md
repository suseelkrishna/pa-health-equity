# Pennsylvania, county by county

Explore **Pennsylvania-relative social vulnerability** and **hospital presence** across 67 counties. This dashboard explores two measures from the broader health-equity study. It does not reproduce the paper's Priority Opportunity Score (POS) findings or create a combined score or priority ranking.

![Public dashboard overview](docs/dashboard-desktop.jpg)

[Research paper](https://suseelkrishna.onrender.com/static/reports/pennsylvania-health-equity-masters-paper.fdd9caa6e888.pdf) · [Portfolio](https://suseelkrishna.onrender.com/). The paper destination matches the [portfolio project page](https://suseelkrishna.onrender.com/work/pennsylvania-health-equity-dashboard/) (verified October 17, 2026). No live dashboard URL or software license has been assigned.

## Setup and verification

Use Python **3.12.14**. From this directory (or a checkout containing exactly its contents):

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. The app loads the six-file `data/releases/v0.2.0-rc1/` bundle and verifies its checksums, source/method metadata, 67 unique county identifiers, source ranges, facility audit, and matching longitude/latitude polygons. It does not ingest or rebuild raw data. `render.yaml` is prepared with `0.0.0.0:$PORT`, automatic deploys disabled, and no service connected.

## Sources and interpretation

- **CDC/ATSDR SVI 2022:** official Pennsylvania-relative county `RPL_THEMES`, based on 2018–2022 ACS estimates. The displayed score is exactly `100 × RPL_THEMES`. Higher means greater vulnerability to hazardous events relative to other Pennsylvania counties. The map scale is fixed at 0–100. [Data](https://svi.cdc.gov/Documents/Data/2022/csv/states_counties/Pennsylvania_county.csv) · [Definitions](https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/10/SVI2022Documentation.pdf).
- **CMS Hospital General Information, February 25, 2026:** 188 unique PA facilities across 58 counties; nine counties have no matching listing. Includes 133 acute care, 26 psychiatric, 17 critical access, seven VA acute care, and five children's facilities. County labels were normalized and all records matched. Counts describe presence, not services, beds, adequacy, or travel distance. [Snapshot archives](https://data.cms.gov/provider-data/archived-data/hospitals).
- **U.S. Census Bureau TIGER/Line 2025:** all 67 PA counties, converted to EPSG:4326 and simplified for display. Statistical boundaries are not legal land descriptions. [Source](https://www2.census.gov/geo/tiger/TIGER2025/COUNTY/).

Source attribution does not imply endorsement by CDC, ATSDR, HHS, CMS, the Census Bureau, or the U.S. Government. [CDC reuse guidance](https://www.cdc.gov/other/agencymaterials.html) · [CMS data guidance](https://data.cms.gov/provider-data/topics/hospitals/about-data).

County summaries can hide differences within counties, and source years differ. Hospital counts and SVI remain separate. Historical paper findings have not been independently reproduced. Table scores show one decimal; CSV downloads preserve source values and full precision.

## Release notes — v0.2.0-rc1

The public bundle has exactly five CSV fields: `county_fips`, `county_name`, `svi_rpl_themes`, `svi_score_0_100`, and `hospital_count`; source and method metadata; and the 67-county map. It contains no Community Conditions source values or derived scores. The earlier three-measure research candidate remains separate and unchanged. Publish only the contents of this directory, not the enclosing research workspace. No raw datasets or local caches are required or included.

## Private first-commit review — October 17, 2026

Copy these **20 files**, preserving their relative paths and including hidden files:

- `.gitignore`, `.python-version`, `README.md`, `app.py`, `requirements.lock`, `render.yaml`.
- `.streamlit/config.toml`.
- `src/pa_public/__init__.py`, `presentation.py`, and `release.py`.
- `tests/test_public_release.py`.
- All six files in `data/releases/v0.2.0-rc1/`.
- All three JPEG screenshots in `docs/`.

All files were reviewed for excluded measure values, raw downloads, personal paths, credential patterns, and accidental artifacts. No such data or credentials were found; explanatory references in this README and exclusion checks in the tests are not source values. The screenshots have no EXIF metadata. Four generated Python cache files were removed; `.gitignore` excludes caches, build outputs, local environment files, Streamlit secrets, raw downloads, and processed caches while retaining the versioned release.

A copy containing only these files passed all 10 tests and the Streamlit application checks on Python 3.12.14 with every locked dependency version verified: two metric options, county selection, search, correct table values, the matching paper link, 67 map features, and 188 facilities. No raw files or research-workspace modules were needed. No blocker remains for a private first commit. This review did not stage, commit, deploy, publish, edit the portfolio, or select a software license.
