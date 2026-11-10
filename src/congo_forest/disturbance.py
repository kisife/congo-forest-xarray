"""Hansen/UMD Global Forest Change access and disturbance summaries."""
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from rasterio.windows import from_bounds

from .config import GFC_BOUNDS, GFC_CACHE, GFC_CREDIT, GFC_TILE, GFC_VERSION
from .spatial import latitude_pixel_area_km2


def gfc_url(layer, tile=GFC_TILE, version=GFC_VERSION):
    return (
        "https://storage.googleapis.com/earthenginepartners-hansen/"
        f"{version}/Hansen_{version}_{layer}_{tile}.tif"
    )


def read_gfc_layer(layer, bounds=GFC_BOUNDS, tile=GFC_TILE):
    """Read only a geographic window from a public Cloud-hosted GeoTIFF."""
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        GDAL_HTTP_MULTIRANGE="YES",
        VSI_CACHE="TRUE",
        CPL_VSIL_CURL_CACHE_SIZE="100000000",
    ):
        with rasterio.open("/vsicurl/" + gfc_url(layer, tile)) as src:
            window = from_bounds(*bounds, src.transform).round_offsets().round_lengths()
            array = src.read(1, window=window)
            return array, src.window_transform(window)


def load_disturbance_subset(cache_path=GFC_CACHE, refresh=False):
    """Load aligned loss-year and data-mask layers for the DRC window."""
    cache_path = Path(cache_path)
    if cache_path.exists() and not refresh:
        return xr.open_dataset(cache_path, engine="scipy", decode_times=False)
    loss, transform = read_gfc_layer("lossyear")
    mask, mask_transform = read_gfc_layer("datamask")
    if transform != mask_transform or loss.shape != mask.shape:
        raise ValueError("GFC layers are not aligned on the same grid.")
    x = transform.c + (np.arange(loss.shape[1]) + 0.5) * transform.a
    y = transform.f + (np.arange(loss.shape[0]) + 0.5) * transform.e
    ds = xr.Dataset(
        data_vars={
            "loss_year": (("y", "x"), loss, {
                "units": "year index (add 2000 for calendar year)",
                "description": "0 = no mapped loss; 1–24 = 2001–2024",
            }),
            "data_mask": (("y", "x"), mask, {
                "description": "0 = no data; 1 = mapped land; 2 = permanent water",
            }),
        },
        coords={
            "x": ("x", x, {"units": "degrees_east"}),
            "y": ("y", y, {"units": "degrees_north"}),
        },
        attrs={
            "title": "Mbandaka, Democratic Republic of the Congo: disturbance window",
            "gfc_version": GFC_VERSION,
            "gfc_tile": GFC_TILE,
            "bounds_wsen": str(GFC_BOUNDS),
            "credit": GFC_CREDIT,
            "processing": "Aligned spatial subsets only; values are unchanged.",
        },
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(cache_path, engine="scipy")
    return ds


def annual_disturbance(ds, start_year=2001, end_year=2024):
    """Return pixel-based mapped disturbance area by year (km²).

    These are map-based descriptive estimates, not design-based area estimates
    with confidence intervals. Water and no-data pixels are excluded.
    """
    y_res = abs(float(ds.y[1] - ds.y[0]))
    x_res = abs(float(ds.x[1] - ds.x[0]))
    area = latitude_pixel_area_km2(ds.y, y_res, x_res).rename({"lat": "y"})
    land = ds.data_mask == 1
    rows = []
    for year in range(start_year, end_year + 1):
        mapped = (ds.loss_year == year - 2000) & land
        rows.append({"year": year, "mapped_disturbance_km2": float((area * mapped).sum())})
    result = pd.DataFrame(rows).set_index("year")
    result["rolling_3yr_mean_km2"] = result.mapped_disturbance_km2.rolling(3, center=True).mean()
    return result.reset_index()
