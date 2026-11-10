"""Reproduce all figures and tables from public data or local caches."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from congo_forest.config import OUTPUT_DIR, BIOMASS_DOI, GFC_VERSION
from congo_forest.biomass import load_biomass_subset, relative_uncertainty, summarize_biomass
from congo_forest.disturbance import load_disturbance_subset, annual_disturbance

FIGURES = OUTPUT_DIR / "figures"
TABLES = OUTPUT_DIR / "tables"
FIGURES.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.titleweight": "bold"})


def save(fig, name):
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", format="svg")
    plt.close(fig)


def biomass_products(ds):
    latest = ds.sel(time=np.datetime64("2024-01-01"))
    uncertainty = relative_uncertainty(ds, 2024)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    latest.agb.plot.imshow(
        x="lon", y="lat", ax=axes[0], cmap="YlGn", vmin=0, vmax=350,
        cbar_kwargs={"label": "Above-ground biomass (Mg ha⁻¹)"},
    )
    axes[0].set_title("ESA CCI Biomass v7.0 — 2024")
    uncertainty.plot.imshow(
        x="lon", y="lat", ax=axes[1], cmap="magma_r", vmin=0, vmax=100,
        cbar_kwargs={"label": "Relative standard deviation (%)"},
    )
    axes[1].set_title("Per-pixel uncertainty — 2024")
    for ax in axes:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect("equal")
    fig.suptitle("Congo Basin regional window (8–32°E, 8°S–6°N)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save(fig, "biomass_and_uncertainty_2024")
    return latest, uncertainty


def disturbance_products(ds):
    annual = annual_disturbance(ds)
    annual.to_csv(TABLES / "annual_disturbance_mbandaka.csv", index=False)
    land = ds.data_mask == 1
    loss = ds.loss_year.where((ds.loss_year > 0) & land)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1, 1.25]})
    image = loss.plot.imshow(
        x="x", y="y", ax=axes[0], cmap="turbo", vmin=1, vmax=24,
        cbar_kwargs={"label": "Year of mapped loss", "ticks": [1, 5, 10, 15, 20, 24]},
    )
    cbar = image.colorbar
    cbar.ax.set_yticklabels([2001, 2005, 2010, 2015, 2020, 2024])
    axes[0].set_title("Mapped stand-replacement loss")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].set_aspect("equal")
    axes[1].bar(annual.year, annual.mapped_disturbance_km2, color="#2b8cbe", label="Annual mapped area")
    axes[1].plot(annual.year, annual.rolling_3yr_mean_km2, color="#d95f02", lw=2, label="3-year rolling mean")
    axes[1].set_title("Annual disturbance summary")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Mapped disturbance (km²)")
    axes[1].set_xticks([2001, 2005, 2010, 2015, 2020, 2024])
    axes[1].legend(frameon=False)
    axes[1].grid(axis="y", alpha=0.2)
    fig.suptitle("Mbandaka window, DRC — Hansen/UMD GFC v1.12", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save(fig, "disturbance_mbandaka_2001_2024")
    return annual


def overview(latest, annual):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    latest.agb.plot.imshow(
        x="lon", y="lat", ax=axes[0], cmap="YlGn", vmin=0, vmax=350,
        cbar_kwargs={"label": "AGB (Mg ha⁻¹)"},
    )
    axes[0].set_title("Above-ground biomass, 2024")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].set_aspect("equal")
    axes[1].bar(annual.year, annual.mapped_disturbance_km2, color="#2b8cbe")
    axes[1].plot(annual.year, annual.rolling_3yr_mean_km2, color="#d95f02", lw=2)
    axes[1].set_title("Mbandaka mapped disturbance")
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("km² per year")
    axes[1].set_xticks([2001, 2005, 2010, 2015, 2020, 2024])
    axes[1].grid(axis="y", alpha=0.2)
    fig.suptitle("Congo Forest xarray | Public-data, reproducible Python analysis", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save(fig, "congo_forest_overview")


def main():
    biomass = load_biomass_subset()
    disturbance = load_disturbance_subset()
    biomass_summary = summarize_biomass(biomass)
    biomass_summary.to_csv(TABLES / "biomass_regional_summary.csv", index=False)
    latest, _ = biomass_products(biomass)
    annual = disturbance_products(disturbance)
    overview(latest, annual)
    peak = annual.loc[annual.mapped_disturbance_km2.idxmax()]
    summary = {
        "biomass": biomass_summary.to_dict(orient="records"),
        "disturbance": {
            "cumulative_mapped_disturbance_km2_2001_2024": float(annual.mapped_disturbance_km2.sum()),
            "peak_year": int(peak.year),
            "peak_year_mapped_disturbance_km2": float(peak.mapped_disturbance_km2),
            "note": "Pixel-based descriptive estimates, not design-based area estimates with confidence intervals.",
        },
        "sources": {"esa_cci_biomass_doi": BIOMASS_DOI, "hansen_gfc_version": GFC_VERSION},
    }
    (TABLES / "analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
