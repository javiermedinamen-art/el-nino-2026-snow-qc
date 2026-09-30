# Depuración SWE / SD — comunicación El Niño 2026 (UPLA)

Carpeta pensada para **compartir / GitHub** (`el-nino-2026-snow-qc`). El pipeline del día a día sigue en [`../cleaning_script/`](../cleaning_script/) dentro del proyecto `ElNiño_2026`.

Cuaderno: [`Snow_QC_Reproducible.ipynb`](Snow_QC_Reproducible.ipynb). Parámetros: [`QC_PARAMETERS.csv`](QC_PARAMETERS.csv).

**Datos de prueba:** `data_ejemplo/` — Portillo (05401007). Clonar solo este repo, `pip install -r requirements.txt`, ejecutar el notebook (salida en `qc_outputs/`).

**Proyecto completo:** con el notebook en `ElNiño_2026/snow_qc_github/`, detecta solo `../Data/Station_SWE/` y `../Data/Station_SnowDepth/`.

```bash
cd snow_qc_github
pip install -r requirements.txt
jupyter notebook Snow_QC_Reproducible.ipynb
```

Scripts batch (mismo flujo): `run_all_qc.py`, etc. Disclosure detallado en `../cleaning_script/README.md`.
