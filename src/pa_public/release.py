"""Validate and load only the public county release; never ingest raw data."""

import csv
import hashlib
import json
import math
from pathlib import Path

RELEASE_ID = "v0.2.0-rc1"
RELEASE_DIRECTORY = Path("data/releases") / RELEASE_ID
FIELDS = ("county_fips", "county_name", "svi_rpl_themes", "svi_score_0_100", "hospital_count")
PA_COUNTY_FIPS = frozenset("42{:03d}".format(n) for n in range(1, 134, 2))
FILES = ("county_inputs.csv", "county_inputs.metadata.json", "pa_counties.geojson", "pa_counties.metadata.json", "sources.json")


class ReleaseError(ValueError):
    """Missing, inconsistent, or invalid public-release input."""


def load_release(repo):
    directory = Path(repo) / RELEASE_DIRECTORY
    try:
        manifest = json.loads((directory / "release.json").read_text())
        if manifest.get("release_id") != RELEASE_ID or manifest.get("county_count") != 67:
            raise ReleaseError("Public release identifier or county count is invalid")
        if set(manifest.get("files", {})) != set(FILES):
            raise ReleaseError("Public release file list must match the intended bundle")
        for name in FILES:
            digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
            if digest != manifest["files"][name]:
                raise ReleaseError("Checksum mismatch for " + name)
        methods = {}
        for data_name, meta_name, method_id in (
            ("county_inputs.csv", "county_inputs.metadata.json", "pa-public-svi-hospital-presence-v1"),
            ("pa_counties.geojson", "pa_counties.metadata.json", "pa-display-boundaries-v1"),
        ):
            meta = json.loads((directory / meta_name).read_text())
            if (meta.get("output_file") != data_name or meta.get("output_sha256") != manifest["files"][data_name]
                    or meta.get("method_id") != method_id or manifest.get("methods", {}).get(data_name) != method_id):
                raise ReleaseError("Method metadata does not match " + data_name)
            methods[data_name] = meta
        sources = json.loads((directory / "sources.json").read_text())["sources"]
        if len(sources) != 3:
            raise ReleaseError("Public release requires exactly three source records")
        source_hashes = {}
        for source in sources:
            if not all(source.get(k) for k in ("provider", "url", "release_date", "retrieval_date", "checksum_sha256", "local_filename")):
                raise ReleaseError("Source metadata is incomplete")
            if len(source["checksum_sha256"]) != 64:
                raise ReleaseError("Invalid source checksum")
            source_hashes[source["local_filename"]] = source["checksum_sha256"]
        references = methods["county_inputs.csv"]["inputs"] + [methods["pa_counties.geojson"]["source"]]
        if len(references) != 3 or any(source_hashes.get(s["local_filename"]) != s["checksum_sha256"] for s in references):
            raise ReleaseError("Method provenance does not match source metadata")
        if methods["pa_counties.geojson"].get("output_crs") != "EPSG:4326":
            raise ReleaseError("Map must use EPSG:4326 longitude/latitude")
        with (directory / "county_inputs.csv").open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != FIELDS:
                raise ReleaseError("County columns must match the public schema exactly")
            rows = list(reader)
        identifiers = [r["county_fips"] for r in rows]
        if len(rows) != 67 or len(set(identifiers)) != 67 or set(identifiers) != PA_COUNTY_FIPS:
            raise ReleaseError("Require exactly 67 unique Pennsylvania county FIPS")
        for row in rows:
            if not row["county_name"].strip():
                raise ReleaseError("County name is missing")
            for field, maximum in (("svi_rpl_themes", 1), ("svi_score_0_100", 100)):
                row[field] = float(row[field])
                if not math.isfinite(row[field]) or not 0 <= row[field] <= maximum:
                    raise ReleaseError("SVI value must be finite and within its source range")
            if not math.isclose(row["svi_score_0_100"], 100 * row["svi_rpl_themes"], rel_tol=0, abs_tol=1e-12):
                raise ReleaseError("SVI score must match the preserved source percentile")
            if not row["hospital_count"].isdigit():
                raise ReleaseError("Hospital count must be a nonnegative integer")
            row["hospital_count"] = int(row["hospital_count"])
        if sum(r["hospital_count"] for r in rows) != methods["county_inputs.csv"]["county_audit"]["unique_facility_ids"]:
            raise ReleaseError("Hospital counts do not match the facility audit")
        geometry = json.loads((directory / "pa_counties.geojson").read_text())
        features = geometry["features"]
        if geometry.get("type") != "FeatureCollection" or len(features) != 67 or {f["id"] for f in features} != PA_COUNTY_FIPS:
            raise ReleaseError("Map must match all 67 county FIPS exactly")
        def check_coordinates(value):
            if not isinstance(value, list) or not value:
                raise ReleaseError("Invalid empty geometry")
            if isinstance(value[0], (float, int)):
                if len(value) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in value) or not (-81 < value[0] < -74 and 39 < value[1] < 43):
                    raise ReleaseError("Invalid Pennsylvania longitude/latitude")
            else:
                for member in value:
                    check_coordinates(member)
        for feature in features:
            if feature["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
                raise ReleaseError("County geometry must be polygons")
            check_coordinates(feature["geometry"]["coordinates"])
        return sorted(rows, key=lambda row: row["county_name"]), geometry
    except ReleaseError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ReleaseError("Missing or invalid public release: " + str(exc)) from exc
