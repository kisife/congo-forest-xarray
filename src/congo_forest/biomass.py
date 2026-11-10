"""ESA CCI Biomass access and descriptive regional summaries."""
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import requests

from .config import BIOMASS_BOUNDS, BIOMASS_CACHE, BIOMASS_URL
from .spatial import latitude_pixel_area_km2


def load_biomass_subset(cache_path=BIOMASS_CACHE, refresh=False):
    """Load the Congo regional window from cache or the public NetCDF Subset Service.

    The source is a 10 km, 18-year global NetCDF. CEDA's NetCDF Subset Service
    transfers only the regional window; no credentials or paid services are required.
    """
    cache_path = Path(cache_path)
    if cache_path.exists() and not refresh:
        return xr.open_dataset(cache_path, engine="scipy")
    west, south, east, north = BIOMASS_BOUNDS
    params = [
        ("var", "agb"), ("var", "agb_sd"),
        ("west", west), ("south", south), ("east", east), ("north", north),
        ("horizStride", 1), ("time_start", "2005-01-01T00:00:00Z"),
        ("time_end", "2024-01-01T00:00:00Z"), ("timeStride", 1),
        ("addLatLon", "true"), ("accept", "netcdf"),
    ]
    response = requests.get(BIOMASS_URL, params=params, timeout=180)
    response.raise_for_status()
    temporary = cache_path.with_suffix(".download.nc")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(response.content)
    with xr.open_dataset(temporary, engine="scipy") as remote:
        subset = remote[["agb", "agb_sd"]].sel(
            lon=slice(west, east), lat=slice(north, south)
        ).load()
    temporary.unlink()
    subset.attrs.update({
        "source_url": BIOMASS_URL,
        "regional_bounds_wsen": str(BIOMASS_BOUNDS),
        "processing": "Spatial subset only; values are unchanged.",
    })
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    subset.to_netcdf(cache_path, engine="scipy")
    return subset


def relative_uncertainty(ds, year=2024):
    """Return AGB standard deviation as a percentage of positive AGB."""
    agb = ds.agb.sel(time=np.datetime64(f"{year}-01-01"))
    sd = ds.agb_sd.sel(time=np.datetime64(f"{year}-01-01"))
    return xr.where(agb > 0, 100 * sd / agb, np.nan).rename("relative_uncertainty")


def summarize_biomass(ds, years=(2010, 2020, 2024)):
    """Calculate descriptive, latitude-area-weighted regional statistics.

    Stock includes all mapped woody above-ground biomass in the rectangular
    window. It is not a forest-only stock and is not converted to carbon.
    """
    lat_res = abs(float(ds.lat[1] - ds.lat[0]))
    lon_res = abs(float(ds.lon[1] - ds.lon[0]))
    area_ha = latitude_pixel_area_km2(ds.lat, lat_res, lon_res) * 100
    rows = []
    for year in years:
        agb = ds.agb.sel(time=np.datetime64(f"{year}-01-01"))
        sd = ds.agb_sd.sel(time=np.datetime64(f"{year}-01-01"))
        valid_area = area_ha.where(agb.notnull()).sum()
        stock_mg = (agb * area_ha).sum()
        positive = agb > 0
        rows.append({
            "year": year,
            "area_weighted_mean_agb_mg_ha": float(stock_mg / valid_area),
            "regional_agb_stock_pg": float(stock_mg / 1e9),
            "high_biomass_area_percent_agb_ge_200": float(
                100 * area_ha.where(agb >= 200).sum() / valid_area
            ),
            "median_relative_uncertainty_percent": float(
                (100 * sd / agb).where(positive).median()
            ),
        })
    return pd.DataFrame(rows)
