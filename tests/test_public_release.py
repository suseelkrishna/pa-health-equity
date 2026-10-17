import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pa_public.release import FIELDS, RELEASE_DIRECTORY, ReleaseError, load_release
from pa_public.presentation import METRICS, county_map, county_table


class PublicReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.directory = self.repo / RELEASE_DIRECTORY
        shutil.copytree(Path(__file__).resolve().parents[1] / RELEASE_DIRECTORY, self.directory)

    def refresh(self):
        manifest_path = self.directory / "release.json"
        manifest = json.loads(manifest_path.read_text())
        for output, meta_name in (("county_inputs.csv", "county_inputs.metadata.json"), ("pa_counties.geojson", "pa_counties.metadata.json")):
            path = self.directory / meta_name
            meta = json.loads(path.read_text())
            meta["output_sha256"] = hashlib.sha256((self.directory / output).read_bytes()).hexdigest()
            path.write_text(json.dumps(meta))
        manifest["files"] = {name: hashlib.sha256((self.directory / name).read_bytes()).hexdigest() for name in manifest["files"]}
        manifest_path.write_text(json.dumps(manifest))

    def change_csv(self, operation):
        path = self.directory / "county_inputs.csv"
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        fields = operation(rows) or FIELDS
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        self.refresh()

    def test_release_map_scales_and_display_precision(self):
        rows, geometry = load_release(self.repo)
        self.assertEqual(len(rows), 67)
        self.assertEqual(sum(r["hospital_count"] for r in rows), 188)
        self.assertEqual(set(METRICS), {"Social Vulnerability", "Hospital Count"})
        self.assertEqual(set(rows[0]), set(FIELDS))
        for metric in METRICS:
            figure = county_map(rows, geometry, metric, "42003")
            self.assertEqual(len(figure.data[0].locations), 67)
            self.assertEqual(list(figure.data[1].locations), ["42003"])
            if metric == "Social Vulnerability": self.assertEqual(figure.data[0].zmax, 100)
        allegheny = next(r for r in rows if r["county_fips"] == "42003")
        self.assertEqual(allegheny["svi_rpl_themes"], .303)
        self.assertEqual(county_table([allegheny])[0]["Social Vulnerability"], 30.3)

    def test_tampering_and_missing_file_fail(self):
        path = self.directory / "county_inputs.csv"
        path.write_text(path.read_text() + "changed")
        with self.assertRaisesRegex(ReleaseError, "Checksum"):
            load_release(self.repo)
        path.unlink()
        with self.assertRaises(ReleaseError): load_release(self.repo)

    def test_missing_or_duplicate_county_fails_after_rehash(self):
        original = (self.directory / "county_inputs.csv").read_bytes()
        self.change_csv(lambda rows: rows.pop() and None)
        with self.assertRaisesRegex(ReleaseError, "67 unique"):
            load_release(self.repo)
        (self.directory / "county_inputs.csv").write_bytes(original)
        self.change_csv(lambda rows: rows.__setitem__(0, dict(rows[1])))
        with self.assertRaisesRegex(ReleaseError, "67 unique"):
            load_release(self.repo)

    def test_extra_column_is_rejected(self):
        def add(rows):
            for row in rows: row["unapproved_measure"] = "1"
            return FIELDS + ("unapproved_measure",)
        self.change_csv(add)
        with self.assertRaisesRegex(ReleaseError, "schema exactly"):
            load_release(self.repo)

    def test_invalid_svi_and_hospital_values_fail(self):
        original = (self.directory / "county_inputs.csv").read_bytes()
        for field, value in (("svi_rpl_themes", "nan"), ("svi_rpl_themes", "1.1"),
                             ("svi_score_0_100", "40"), ("hospital_count", "-1"), ("hospital_count", "1.5")):
            with self.subTest(field=field, value=value):
                (self.directory / "county_inputs.csv").write_bytes(original)
                self.change_csv(lambda rows: rows[0].update({field: value}))
                with self.assertRaises(ReleaseError): load_release(self.repo)

    def test_audit_total_must_match(self):
        self.change_csv(lambda rows: rows[0].update({"hospital_count": "2"}))
        with self.assertRaisesRegex(ReleaseError, "facility audit"):
            load_release(self.repo)

    def test_projected_coordinates_fail(self):
        path = self.directory / "pa_counties.geojson"
        geo = json.loads(path.read_text()); geo["features"][0]["geometry"] = {"type": "Polygon", "coordinates": [[[100000, 200000]]]}
        path.write_text(json.dumps(geo)); self.refresh()
        with self.assertRaisesRegex(ReleaseError, "longitude/latitude"):
            load_release(self.repo)

    def test_geo_county_mismatch_fails_after_rehash(self):
        path = self.directory / "pa_counties.geojson"
        geo = json.loads(path.read_text()); geo["features"][0]["id"] = "01001"
        path.write_text(json.dumps(geo)); self.refresh()
        with self.assertRaisesRegex(ReleaseError, "67 county"):
            load_release(self.repo)

    def test_source_method_link_fails_after_rehash(self):
        path = self.directory / "sources.json"
        sources = json.loads(path.read_text()); sources["sources"][0]["checksum_sha256"] = "0" * 64
        path.write_text(json.dumps(sources)); self.refresh()
        with self.assertRaisesRegex(ReleaseError, "provenance"):
            load_release(self.repo)

    def test_public_bundle_contains_only_approved_fields(self):
        for path in self.directory.iterdir():
            text = path.read_text().lower()
            self.assertNotIn("chr_", text)
            self.assertNotIn("community conditions", text)


if __name__ == "__main__":
    unittest.main()
