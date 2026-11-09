import sys
from pathlib import Path
import unittest
import tempfile
import pandas as pd

import geopandas as gpd
from shapely.geometry import Point, Polygon, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from clean_data import clean_vector, clean_choices, METRIC_CRS


class CleaningChecks(unittest.TestCase):
    def test_colocated_addresses_are_retained_and_flagged(self):
        frame = gpd.GeoDataFrame({"OBJECTID": [1, 2], "ADDRESS": [" A ", "B"]},
            geometry=[Point(500000, 3650000)] * 2, crs=METRIC_CRS)
        core = box(499900, 3649900, 500100, 3650100)
        good, quarantine, stats = clean_vector(frame, "OBJECTID", "Point", core, core)
        self.assertEqual(len(good), 2)
        self.assertTrue(good.duplicate_geometry.all())
        self.assertEqual(good.address.iloc[0], "A")
        self.assertTrue(quarantine.empty)

    def test_invalid_polygon_is_repaired_and_missing_geometry_quarantined(self):
        bowtie = Polygon([(500000, 3650000), (500010, 3650010), (500010, 3650000), (500000, 3650010)])
        frame = gpd.GeoDataFrame({"OBJECTID": [1, 2]}, geometry=[bowtie, None], crs=METRIC_CRS)
        core = box(499900, 3649900, 500100, 3650100)
        good, quarantine, stats = clean_vector(frame, "OBJECTID", "Polygon", core, core)
        self.assertEqual(len(good), 1)
        self.assertTrue(good.geometry.is_valid.all())
        self.assertAlmostEqual(good.area_m2.iloc[0], 50)
        self.assertEqual(len(quarantine), 1)
        self.assertEqual(stats["repaired_rows"], 1)

    def test_duplicate_source_id_is_not_silently_discarded(self):
        frame = gpd.GeoDataFrame({"OBJECTID": [1, 1]}, geometry=[Point(0, 0), Point(1, 1)], crs=METRIC_CRS)
        with self.assertRaises(ValueError):
            clean_vector(frame, "OBJECTID", "Point", box(-1, -1, 2, 2), box(-1, -1, 2, 2))

    def test_invalid_behavioral_label_is_quarantined_and_controls_retained(self):
        rows = []
        for i in range(3):
            row = {"Participant": f"P{i}", "Trial": 1, "TS": 1560000000,
                   "B_chosen": 0 if i < 2 else 7, "Treatment": 1 if i == 0 else 0}
            for r in ["A", "B"]:
                row.update({f"{r}_length": 100, f"{r}_sun_length": 40,
                            f"{r}_tree_length": 20, f"{r}_shade_length": 40})
            rows.append(row)
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pd.DataFrame(rows).to_csv(folder / "behavioural_data.csv", index=False)
            report = clean_choices(folder, folder)
            self.assertEqual(report["clean_rows"], 2)
            self.assertEqual(report["sun_present_rows"], 1)
            self.assertEqual(report["quarantined_rows"], 1)
            clean = pd.read_csv(folder / "singapore_choices.csv")
            self.assertEqual(clean.treatment.tolist(), [1, 0])


if __name__ == "__main__":
    unittest.main()
