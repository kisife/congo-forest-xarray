"""Spatial helpers for geographic latitude/longitude grids."""
import numpy as np
import xarray as xr


def latitude_pixel_area_km2(lat, lat_resolution, lon_resolution):
    """Return spherical pixel area (km²) for each latitude cell centre.

    Uses the WGS84 mean Earth radius and exact latitude cell edges. Longitude
    and latitude resolutions are supplied in decimal degrees.
    """
    earth_radius_km = 6371.0088
    lat = np.asarray(lat, dtype=float)
    north = np.deg2rad(lat + abs(lat_resolution) / 2)
    south = np.deg2rad(lat - abs(lat_resolution) / 2)
    dlon = np.deg2rad(abs(lon_resolution))
    area = earth_radius_km**2 * dlon * (np.sin(north) - np.sin(south))
    return xr.DataArray(area, coords={"lat": lat}, dims="lat", name="pixel_area_km2")
