import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from congo_forest.biomass import relative_uncertainty, summarize_biomass
from congo_forest.disturbance import annual_disturbance
from congo_forest.spatial import latitude_pixel_area_km2


class SpatialTests(unittest.TestCase):
    def test_equatorial_pixel_area(self):
        area = latitude_pixel_area_km2([0.0], 0.1, 0.1)
        self.assertAlmostEqual(float(area[0]), 123.64, places=1)

    def test_pixel_area_decreases_toward_poles(self):
        area = latitude_pixel_area_km2([0.0, 60.0], 0.1, 0.1)
        self.assertLess(float(area[1]), float(area[0]))


class DisturbanceTests(unittest.TestCase):
    def setUp(self):
        self.ds = xr.Dataset(
            {
                "loss_year": (("y", "x"), np.array([[1, 1], [2, 0]], dtype=np.uint8)),
                "data_mask": (("y", "x"), np.ones((2, 2), dtype=np.uint8)),
            },
            coords={"y": [0.000125, -0.000125], "x": [18.000125, 18.000375]},
        )

    def test_annual_disturbance_conserves_total(self):
        annual = annual_disturbance(self.ds, 2001, 2002)
        self.assertEqual(len(annual), 2)
        self.assertGreater(annual.loc[0, "mapped_disturbance_km2"], 0)
        self.assertAlmostEqual(
            annual.loc[0, "mapped_disturbance_km2"],
            2 * annual.loc[1, "mapped_disturbance_km2"],
            places=8,
        )

    def test_water_is_excluded(self):
        self.ds.data_mask.values[0, 0] = 2
        annual = annual_disturbance(self.ds, 2001, 2002)
        self.assertAlmostEqual(
            annual.loc[0, "mapped_disturbance_km2"],
            annual.loc[1, "mapped_disturbance_km2"],
            places=8,
        )


class BiomassTests(unittest.TestCase):
    def test_summary_and_relative_uncertainty(self):
        times = pd.to_datetime(["2010-01-01", "2020-01-01", "2024-01-01"])
        ds = xr.Dataset(
            {
                "agb": (("time", "lat", "lon"), np.full((3, 2, 2), 250.0)),
                "agb_sd": (("time", "lat", "lon"), np.full((3, 2, 2), 50.0)),
            },
            coords={"time": times, "lat": [0.05, -0.05], "lon": [20.05, 20.15]},
        )
        summary = summarize_biomass(ds)
        self.assertEqual(len(summary), 3)
        self.assertTrue((summary.regional_agb_stock_pg > 0).all())
        self.assertTrue(np.allclose(summary.high_biomass_area_percent_agb_ge_200, 100))
        self.assertAlmostEqual(float(relative_uncertainty(ds).median()), 20.0)
        self.assertNotIn("time", relative_uncertainty(ds).dims)


if __name__ == "__main__":
    unittest.main()
