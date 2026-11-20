# El Niño 2026 — extra data and return-period code

Bits that were not in the 2010–2024 Zenodo snow-depth deposit (https://doi.org/10.5281/zenodo.21577171).

- `data/station_sd/SD_extension_2025_2026.csv` — daily snow depth for 2025–2026 (cm), five stations
- `data/station_swe/` — quality-controlled daily SWE (mm)
- `code/frequency_analysis/` — Pearson Type III return-period scripts used in the paper

```bash
pip install -r requirements.txt
cd code/frequency_analysis
python 04_return_period_steven.py
```

Paths assume the CSVs under `data/`. Snowcourse/ONI inputs are not bundled here; get those from the usual DGA / CPC sources if you want to re-run everything.
