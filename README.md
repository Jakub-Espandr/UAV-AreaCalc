<p align="center">
  <a href="https://i.ibb.co/JjDLn9Py/icon.png">
    <img src="https://i.ibb.co/JjDLn9Py/icon.png" alt="UAV AreaCalc Logo" width="220"/>
  </a>
</p>

<h1 align="center">UAV AreaCalc – TIFF + Shapefile Area Calculator</h1>
<p align="center"><em>Created by Jakub Ešpandr | FlyCamCzech | Born4Flight</em></p>

---

## 🛰️ Overview

**UAV AreaCalc** is a lightweight cross-platform desktop application for calculating the area of non-transparent regions in UAV-acquired GeoTIFFs (with alpha channel) and comparing them to user-defined regions of interest (ROIs) in Shapefiles.

It is designed for fast validation and visualization of aerial image coverage and analysis zones directly from high-resolution raster data.

---

## ✨ Features

- **Area Calculation**
  - Calculates area of visible (non-transparent) regions from alpha-enabled TIFF imagery.
  - Calculates total area from Esri Shapefile polygons (ROI).
  - Supports units in hectares (ha) or square meters (m²).

- **Map Visualization**
  - Downsampled TIFF preview with high-speed rendering.
  - Overlays two color-coded semi-transparent polygons:
    - Red: TIFF mask extent
    - Blue: ROI from shapefile
  - Clean map layout for screenshots or reporting (no axis/grid clutter).

- **User Interface**
  - Intuitive GUI built with PySide6.
  - Interactive file selection dialogs for TIFF and `.shp`.
  - Real-time area output and unit switcher (radio buttons).
  - Resizable split layout with control panel and map canvas.

---

## 📦 Requirements

```
PySide6>=6.0.0         # Modern GUI framework
matplotlib==3.9.3      # Map visualization
geopandas==1.0.1       # Shapefile and vector handling
rasterio==1.3.10       # GeoTIFF handling
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/Jakub-Espandr/UAVAreaCalc.git
cd UAV-AreaCalc
pip install -r requirements.txt
python main.py
```

---

## 🛠️ Usage

1. Launch the app with `python main.py`
2. Click **"Browse GeoTIFF"** and select an alpha-enabled `.tif`
3. Click **"Browse Shapefile"** to add your ROI
4. The map will display both overlays
5. Toggle between hectares or square meters in the unit panel

---

## 📌 Changelog

See [CHANGELOG.md](https://github.com/Jakub-Espandr/UAVAreaCalc/blob/main/CHANGELOG.md)

---

## 📁 Project Structure

```
UAV-AreaCalc/
├── main.py
├── ui/              # GUI layout and styling
├── core/            # Area calculation logic
├── utils/           # Helper functions (geometry, conversion)
├── assets/
│   └── fonts/       # Custom font definitions
│   └── icons/       # Custom icons definitions
├── requirements.txt
└── CHANGELOG.md
```

---

## 🔐 License

This project is licensed under the **Non-Commercial Public License (NCPL v1.0)**  
© 2025 Jakub Ešpandr – FlyCamCzech, Born4Flight

See the full [LICENSE](https://github.com/Jakub-Espandr/UAV-AreaCalc/blob/main/LICENSE) for terms.

---

## 🙏 Acknowledgments

- Built using open-source geospatial libraries: Rasterio, GeoPandas, PySide6.
