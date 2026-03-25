# GeoDiagnostic

<p align="center">
  <img src="geodiagnostic/icon.png" width="80" alt="GeoDiagnostic logo"/>
</p>

<p align="center">
  <strong>Automated geospatial environmental diagnostics using Google Earth Engine</strong><br/>
  Free and open source QGIS plugin · Version 1.0.7 · Lenin E. Julca
</p>

<p align="center">
  <a href="https://plugins.qgis.org/plugins/geodiagnostic/"><img src="https://img.shields.io/badge/QGIS-Plugin%20Repository-green?logo=qgis"/></a>
  <a href="https://www.gnu.org/licenses/gpl-2.0"><img src="https://img.shields.io/badge/License-GPL%20v2-blue.svg"/></a>
  <img src="https://img.shields.io/badge/QGIS-3.16%2B-green"/>
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue"/>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey"/>
</p>

---

## What is GeoDiagnostic?

**GeoDiagnostic** is a free QGIS plugin that automates the generation of geospatial environmental baseline diagnostics by connecting to **Google Earth Engine (GEE)** as a cloud computing engine. It calculates multiple environmental variables within any area of interest (AOI) defined by the user, and exports the results as `.tif` raster files that are automatically loaded in QGIS with predefined color palettes.

The plugin generates a complete technical PDF report with charts, statistics, methodology, and bibliographic references — ready to be used in academic theses, technical reports, and environmental impact assessments.

---

## Key Features

| Module | Variables | Source | Resolution |
|--------|-----------|--------|-----------|
| **Topography** | DEM, slope, aspect, TWI | SRTM v3 | 30 m |
| **Vegetation** | NDVI, EVI, SAVI, NDWI, NDMI, NBR, BSI | Sentinel-2 SR | 10 m |
| **Land Cover** | 9 classes (Dynamic World) | Google/WRI | 10 m |
| **Precipitation** | Monthly series, annual total | CHIRPS v2.0 | 5 km |
| **Temperature** | Mean, min, max monthly | ERA5-Land | 11 km |
| **Soils** | pH, texture (USDA class), carbon, bulk density | SoilGrids 250m | 250 m |
| **Erosion** | RUSLE index (R·LS·C) | SRTM+CHIRPS+DW | 30 m |
| **Evapotranspiration** | ET real (8-day) | MOD16 MODIS | 500 m |

**Additional features:**
- AOI technical sheet: area (ha/km²), perimeter, centroid, UTM coordinates, bounding box
- Administrative location (country, department, district) via FAO GAUL
- Dual export mode: direct download (<8,000 ha) or Google Drive (>8,000 ha)
- Professional PDF report with charts, statistics, methodology and APA references
- Automatic color palettes for all output rasters
- Plugin minimizes automatically when drawing AOI polygon

---

## Requirements

### Software
- **QGIS 3.16** or higher (tested on QGIS 3.44 Solothurn)
- **Python 3.9+** (included with QGIS)
- **earthengine-api** Python library (see installation below)

### Accounts (free)
- **Gmail account** registered at [earthengine.google.com](https://earthengine.google.com)
- **Google Cloud Project** with Earth Engine API enabled ([console.cloud.google.com](https://console.cloud.google.com))

---

## Installation

### Step 1 — Install the plugin in QGIS

1. Download the latest ZIP from the [Releases](https://github.com/ljulcaoepg19-gif/geodiagnostic/releases) section
2. Open QGIS → **Plugins** → **Manage and Install Plugins**
3. Click **Install from ZIP** → select the downloaded ZIP
4. Click **Install Plugin**
5. The plugin appears under **Web → GeoDiagnostic**

### Step 2 — Install earthengine-api

GeoDiagnostic requires the `earthengine-api` library in QGIS's internal Python environment.

**Option A — OSGeo4W Shell (recommended for Windows):**
```bash
pip install earthengine-api
```

**Option B — QGIS Python Console (universal):**
```python
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "earthengine-api"], check=True)
```
Open via: Plugins → Python Console (Ctrl+Alt+P), paste the code and press Enter. Restart QGIS.

**Verify installation:**
```python
import ee
print(ee.__version__)  # Should print 1.7.x or higher
```

### Step 3 — Authenticate with Google Earth Engine

1. Open GeoDiagnostic → **Config GEE** tab
2. Enter your Gmail address and Google Cloud Project ID
3. Click **Authenticate with Google** — your browser opens
4. Accept Google permissions → return to QGIS
5. Click **Verify connection** → green indicator appears
6. Click **Save configuration**

---

## Usage

1. **Define AOI** — load a vector layer or draw a polygon on the map
2. **Set analysis period** — start and end dates
3. **Select modules** — check the variables to calculate
4. **Run** — click **Execute GeoDiagnostic**
5. **Results** — rasters load automatically in QGIS, results appear in the Results tab
6. **PDF Report** — click **Generate PDF Report** in the Results tab

For detailed instructions, see the [User Manual](geodiagnostic/manual.pdf) included in the plugin.

---

## Output Files

All output files are saved in the configured output folder under a subfolder named after your project:

```
OutputFolder/
  ProjectName/
    ProjectName_DEM.tif
    ProjectName_Slope.tif
    ProjectName_NDVI.tif
    ProjectName_LandCover.tif
    ProjectName_Precipitation.tif
    ProjectName_Temperature.tif
    ProjectName_SoilPH.tif
    ProjectName_Carbon.tif
    ProjectName_RUSLE.tif
    ProjectName_ET.tif
    ProjectName_Report.pdf
    ProjectName_AOISheet.txt
```

---

## Area Limits

| Area range | Mode | Resolution | Est. time |
|-----------|------|-----------|----------|
| < 1 ha | Warning (low pixel count) | Maximum | < 5 sec |
| 1 – 8,000 ha | **Direct download** (automatic) | Maximum | 10–60 sec |
| 8,000 – 50,000 ha | **Google Drive export** | Reduced (90m) | 2–10 min |
| > 50,000 ha | Google Drive (large area warning) | Reduced | > 10 min |

---

## Supported Geometry Types

- Single Polygon (Shapefile, GeoJSON, KML)
- MultiPolygon (Shapefile, GeoJSON, KML) — automatically handled
- Drawn polygon (interactive on QGIS canvas)

---

## Data Sources

| Dataset | Variable | Provider | License |
|---------|----------|----------|---------|
| SRTM v3 | Topography | NASA/USGS | Public domain |
| Sentinel-2 SR Harmonized | Vegetation | ESA/Copernicus | Free use |
| CHIRPS v2.0 | Precipitation | UCSB CHG | Free use |
| ERA5-Land | Temperature | ECMWF/Copernicus | Free use |
| SoilGrids 250m | Soil properties | ISRIC | CC-BY 4.0 |
| Dynamic World | Land cover | Google/WRI | CC-BY 4.0 |
| MOD16A2GF | Evapotranspiration | NASA/MODIS | Free use |
| FAO GAUL | Administrative boundaries | FAO | Non-commercial |

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `No module named 'ee'` | earthengine-api not installed | Follow Step 2 above |
| `Project not found` | Wrong Project ID | Check ID in Google Cloud Console |
| `Permission denied` | GEE account not approved | Register at earthengine.google.com |
| `MultiPolygon error` | Complex KML geometry | Plugin handles automatically in v1.0.8+ |
| `Too many pixels` | AOI too large | Plugin reduces scale automatically |
| `No GEE connection on open` | Expired credentials | Re-authenticate in Config GEE tab |

---

## Changelog

### v1.0.0 — Versión Final (Marzo 2026)
- **FIX CRÍTICO:** Recorte exacto al perímetro del polígono — el GPKG de máscara ahora se guarda siempre en WGS84 (EPSG:4326), coincidiendo con el CRS de los rasters GEE. Se agrega `ALL_TOUCHED=True` para incluir píxeles de borde. Antes las capas no se cortaban exactamente al SHP.
- **FIX GEE:** `updateMask` aplicado antes de descargar — GEE ahora envía solo los píxeles dentro del AOI con NoData exterior, reduciendo el tamaño del archivo y mejorando la precisión.
- **NUEVO:** Tabla de coordenadas de vértices en el reporte PDF — muestra Latitud/Longitud WGS84 y Este/Norte UTM para cada vértice del polígono. Para polígonos con más de 50 vértices se muestra tabla resumida.
- **NUEVO:** Botón "Exportar vértices (.csv)" en la ficha AOI — genera un CSV con todos los vértices en ambos sistemas de referencia.
- **FIX REPORTE:** La recomendación general del diagnóstico ahora es dinámica — antes siempre decía "condiciones favorables" (if True hardcodeado). Ahora evalúa pendiente, pH, erosión y precipitación reales.
- **FIX MANUAL:** Sección 4 (instalación earthengine-api) completamente reescrita con instrucciones separadas para Windows, Linux y macOS, pasos numerados y mensajes de verificación.
- **MEJORA:** Advertencia visible en la tabla de resultados cuando el recorte de un raster falla (antes fallaba silenciosamente cargando el raster sin recortar).

- Added evapotranspiration module (MOD16)
- Added 6 new spectral indices: EVI, SAVI, NDWI, NDMI, NBR, BSI
- Complete soil module: texture (USDA class), bulk density, carbon
- Professional PDF report with charts, statistics and APA references
- Dual export mode: direct download / Google Drive
- Plugin minimizes when drawing AOI polygon
- Yape/Plin donation block in About tab and PDF report

### v1.0.6 (March 2026)
- Author data updated: Lenin E. Julca
- Removed test area button
- Fixed QgsRubberBand API for QGIS 3.44

### v1.0.5 (March 2026)
- Fixed MultiPolygon import error
- Fixed plugin folder name conflict
- Fixed QgsRubberBand type argument

### v1.0.4 (March 2026)
- Updated About tab with real author data
- Added +51 prefix to phone number
- Fixed Python cache conflict on reinstall

### v1.0.3 (March 2026)
- Added AOI technical sheet panel
- Added fixed output folder (Option A)
- Added pine tree icon
- Full Spanish description in metadata

### v1.0.0–1.0.2 (March 2026)
- Initial release with GEE connection
- Basic topography, vegetation, climate, soil modules
- Area test button (Cajamarca ~500 ha)

---

## Contributing

Contributions, bug reports and feature suggestions are welcome! Please use the [Issues](https://github.com/ljulcaoepg19-gif/geodiagnostic/issues) section.

---

## Citation

If you use GeoDiagnostic in your research or technical work, please cite it as:

```
Julca, L. E. (2026). GeoDiagnostic: Automated geospatial environmental diagnostics
using Google Earth Engine (Version 1.0.7) [QGIS Plugin].
https://github.com/ljulcaoepg19-gif/geodiagnostic
```

---

## Author & Support

**Lenin E. Julca**
Remote Sensing and GIS Specialist

📧 ljulcao_epg19@unc.edu.pe
📱 +51 976 742 241

---

## Support the Project

GeoDiagnostic is free and open source. If it helped you in your project, thesis or professional work, you can support its development:

**📲 Yape or Plin: +51 976 742 241 — Lenin E. Julca**

*Any amount is welcome and greatly appreciated. Your support makes it possible to keep developing free tools for the Latin American GIS community.*

---

## License

This project is licensed under the **GNU General Public License v2.0** — see the [LICENSE](LICENSE) file for details.

This plugin uses Google Earth Engine, which requires a separate free account at [earthengine.google.com](https://earthengine.google.com). The `earthengine-api` library is licensed under the Apache License 2.0.
