# El Niño 2026 snow data and scripts

Daily snow depth and SWE from the five automatic DGA stations used in our Glacies note (Quebrada Larga, Portillo, Laguna Negra, Termas del Flaco, Lo Aguirre), plus the scripts we used for cleaning and return periods.

The older snow depth series (2010–2024) is already on Zenodo: https://doi.org/10.5281/zenodo.21577171  
This repo adds the 2025–2026 depth extension, the QC’d SWE, and the analysis code.

## Data

- `data/station_sd/` — daily snow depth (cm). `all_stations_SD.csv` has one column per site; `SD_extension_2025_2026.csv` is just 2025–2026. Individual station files are there too.
- `data/station_swe/` — same layout for SWE (mm), after QC.
- `data/snowcourses/` — manual surveys.
- `data/enso/` — ONI v6 seasonal values.
- `data/PORTILLO_SD_SWE.csv` — Portillo automatic series with snowcourse columns side by side.

Snow depth through 2024 comes from the Southern Andes dataset (Caro et al.). We appended DGA exports for 2025–2026; we did not re-run their full QC on that extension (only a small abrupt-zero check at Laguna Negra). SWE was cleaned with the MAD / rolling-median steps described in `QC_PARAMETERS.csv` and `code/cleaning/README.md`.

## Code

- `code/cleaning/` — SWE cleaning and the site-specific SD/SWE checks.
- `code/frequency_analysis/` — Pearson Type III return periods (`04_return_period_steven.py`).
- `notebooks/Snow_QC_Reproducible.ipynb` — walk-through of the SWE QC on example files.

```bash
pip install -r requirements.txt

# return periods
cd code/frequency_analysis
python 04_return_period_steven.py
# plots go to ../../figures, tables to ../../outputs
```

If something path-related breaks, open `code/frequency_analysis/paths.py` — everything is meant to be relative to this folder.
