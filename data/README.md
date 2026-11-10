# Data access

Large source files and local caches are intentionally not committed. Run
`python scripts/reproduce.py` from the repository root to create the two caches
in `data/processed/` and regenerate every figure and table.

## ESA CCI Biomass v7.0

- Product: global above-ground biomass (AGB) and AGB standard deviation.
- Access: public CEDA NetCDF Subset Service; no account required.
- Source resolution used here: 10 km (0.1°).
- Years: 2005–2012 and 2015–2024.
- Spatial subset: 8–32°E, 8°S–6°N, referred to as the **Congo Basin regional window**.
- DOI: https://doi.org/10.5285/6429d1aafe1e43b9b414e4a5a7f8b903
- Terms: https://artefacts.ceda.ac.uk/licences/specific_licences/esacci_biomass_terms_and_conditions_v2.pdf

The analysis subsets values but does not alter them. AGB is reported in Mg ha⁻¹.
The rectangular regional window is not an exact hydrological basin boundary.

## Hansen/UMD Global Forest Change v1.12

- Product: 30 m `lossyear` and `datamask` GeoTIFF layers.
- Access: public Google Cloud Storage; no account required.
- Tile: `10N_010E`.
- Spatial subset: 18.0–18.5°E, 0.0–0.5°N, near Mbandaka, DRC.
- Years represented: first mapped stand-replacement loss in 2001–2024.
- Download: https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html
- Credit: **Hansen/UMD/Google/USGS/NASA**.
- License: CC BY 4.0.

Only the required spatial windows are read remotely. The code does not download
the full 630 MB tree-cover tile and does not calculate a forest-baseline loss
percentage.
