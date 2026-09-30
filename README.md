# Automatic snow data quality control (UPLA El Niño 2026)

Publication disclosure for daily **snow depth (SD)** and **snow water equivalent (SWE)** cleaning applied in the El Niño 2026 Brief Report. Machine-readable parameters: `QC_PARAMETERS.csv`.

## Reproducible notebook (reviewers)

**Start here:** [`Snow_QC_Reproducible.ipynb`](Snow_QC_Reproducible.ipynb) — single file with markdown + all QC code. Run from the repository root (needs `Data/Station_SWE/` and `Data/Station_SnowDepth/`). Install deps: `pip install -r cleaning_script/requirements.txt`.

Set `WRITE_FILES = False` in the notebook to write only to `cleaning_script/qc_outputs/` without modifying `Data/`.

**Legacy reference:** full multi-basin workflow in `Depuracion_SD.ipynb` (internal). The Python scripts below mirror the notebook and are used in `analysis/scripts/00_run_pipeline.py`.

## Run order (matches `analysis/scripts/00_run_pipeline.py`)

```bash
cd /path/to/ElNiño_2026
python cleaning_script/run_all_qc.py
```

Or step by step:

1. `python cleaning_script/clean_swe_automatic.py` — all automatic SWE CSVs under `Data/Station_SWE/`
2. `python cleaning_script/apply_sd_qc.py` — Laguna Negra SD abrupt zeros
3. `python cleaning_script/apply_quebrada_swe_qc.py` — Quebrada Larga 2026 pillow SWE vs SD

Original SWE files are copied once to `Data/Station_SWE/_original_backup/`; cleaning always re-reads from backup when present.

## Table 1. Snow depth (SD) processing

| Item | Treatment |
|------|-----------|
| Historical SD | Southern Andes Snow Depth Dataset (Caro et al., 2026), quality-controlled compilation |
| 2026 SD | DGA automatic exports appended through 31 August 2026 |
| Lo Aguirre / Termas / others | Use `SD_mean_clean` from source CSV (negative raw values may be set to 0 where documented in source) |
| Laguna Negra (05703009) | **Additional QC:** if `SD_mean_clean = 0` while previous valid depth (forward-fill up to **3 days**) was **> 50 cm**, set clean (and raw if 0) to missing |

Implementation: `sd_qc_utils.qc_laguna_negra_zeros`, `apply_sd_qc.py`.

## Table 2. SWE cleaning pipeline (all five automatic SWE stations)

Applied to columns `min`, `media`, `max` when present.

| Step | Description |
|------|-------------|
| 1 | Clip negatives to **0** |
| 2 | Null values **> station max** (Table 3) |
| 3 | **MAD spike detection** (window **7 days**, `fwindow = 3`): flag isolated spikes where robust z > **k**, neighbor jumps exceed **k × MAD**, and absolute step test (see `swe_clean_utils.detect_spikes_mad`) |
| 4 | Interpolate gaps ≤ **2 days**, then **centered rolling median** (`smooth_window`) |
| 5 | Clip negatives to **0** again |

Implementation: `swe_clean_utils.py`, `clean_swe_automatic.py`.

## Table 3. SWE station parameters

| Station | ID | Max SWE (mm) | fwindow | k (MAD) | abs_thr (mm) | smooth (days) | Notes |
|---------|-----|--------------|---------|---------|--------------|---------------|--------|
| Quebrada Larga | 04520006 | 3500 | 3 | 4.0 | 100 | 3 | Pillow; + Table 4 |
| Portillo | 05401007 | 1200 | 3 | 3.5 | 75 | 9 | Pillow |
| Laguna Negra | 05703009 | 3000 | 3 | 4.0 | 100 | 3 | Snow scale |
| Termas del Flaco | 06020001 | 1200 | 3 | 4.0 | 100 | 3 | Snow scale |
| Lo Aguirre | 07301000 | 1200 | 3 | 4.0 | 100 | 3 | Snow scale |

Constants: `station_qc_config.py`.

## Table 4. Quebrada Larga pillow SWE vs snow depth (2026 only)

Same-day `SD_mean_clean` and SWE `media`. Failing days: `media` set to missing.

| Rule | Condition |
|------|-----------|
| Sign / magnitude | SWE < 0 or \|SWE\| > 3500 mm |
| Depth required | SD missing or SD < **50 cm** |
| Density-like ratio | SD ≥ **10 cm** and SWE/SD not in **[0.05, 12.5]** (SWE in mm, SD in cm) |
| Shallow pack | **5 cm ≤ SD < 10 cm** and SWE > **40 mm** |

Implementation: `sd_qc_utils.qc_quebrada_larga_swe`, `apply_quebrada_swe_qc.py`.

## Files in this folder

| File | Role |
|------|------|
| `station_qc_config.py` | All numeric parameters |
| `QC_PARAMETERS.csv` | Supplement-style parameter table |
| `swe_clean_utils.py` | MAD spike + smoothing functions |
| `sd_qc_utils.py` | Laguna SD + Quebrada SWE rules |
| `clean_swe_automatic.py` | Batch SWE cleaning |
| `apply_sd_qc.py` | Laguna Negra SD in-place |
| `apply_quebrada_swe_qc.py` | Quebrada Larga SWE in-place |
| `run_all_qc.py` | Full sequence |
| `Depuracion_SD.ipynb` | Extended historical cleaning workflow (not all steps used in paper) |

## Suggested Methods sentence (SWE)

*Daily SWE from DGA SNIA was cleaned by clipping non-physical values, removing isolated spikes with a robust median/MAD filter (parameters in Supplementary Table Sx), and applying a short rolling-median smooth (Table Sx). Quebrada Larga pillow SWE in 2026 was screened against co-located snow depth using the rules in Table Sx. SWE was set to zero when the 7-day maximum snow depth was below 2 cm, with brief gap infilling during accumulation (see processing scripts).*

Replace **Sx** with your Glacies supplementary table number pointing to `QC_PARAMETERS.csv` or a formatted table derived from this README.
