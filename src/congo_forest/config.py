"""Project configuration and public data endpoints."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"

BIOMASS_URL = (
    "https://dap.ceda.ac.uk/thredds/ncss/neodc/esacci/biomass/data/agb/maps/"
    "v7.0/netcdf/ESACCI-BIOMASS-L4-AGB-MERGED-10000m-fv7.0.nc"
)
BIOMASS_DOI = "https://doi.org/10.5285/6429d1aafe1e43b9b414e4a5a7f8b903"
BIOMASS_BOUNDS = (8.0, -8.0, 32.0, 6.0)  # west, south, east, north
BIOMASS_CACHE = DATA_DIR / "congo_biomass_10km_v7.nc"

GFC_VERSION = "GFC-2024-v1.12"
GFC_TILE = "10N_010E"
GFC_BOUNDS = (18.0, 0.0, 18.5, 0.5)  # Mbandaka window, DRC
GFC_CACHE = DATA_DIR / "mbandaka_disturbance.nc"
GFC_CREDIT = "Hansen/UMD/Google/USGS/NASA"
