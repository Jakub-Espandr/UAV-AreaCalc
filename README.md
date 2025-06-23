<p align="center">
  <a href="https://i.ibb.co/JjDLn9Py/icon.png">
    <img src="https://i.ibb.co/JjDLn9Py/icon.png" alt="UAV AreaCalc Logo" width="220"/>
  </a>
</p>

<h1 align="center">UAV AreaCalc – TIFF + Shapefile Area Calculator</h1>
<p align="center"><em>Created by Jakub Ešpandr | FlyCamCzech | Born4Flight</em></p>


<p align="center">
  <a href="https://ibb.co/wZSzWCXx">
    <img src="https://i.ibb.co/Ng9yjpPH/UAVArea-Calculator.png" alt="UAV AreaCalc Screenshot" width="50%"/>
  </a>
</p>

---

## 🛰️ Overview

**UAV AreaCalc** is a lightweight cross-platform desktop application for calculating the area of non-transparent regions in UAV-acquired GeoTIFFs (with alpha channel) and comparing them to user-defined regions of interest (ROIs) in Shapefiles.

It is designed for fast validation and visualization of aerial image coverage and analysis zones directly from high-resolution raster data, with **worldwide geographic support** that automatically adapts to any region's coordinate system.

---

## ✨ Features

- **Area Calculation**
  - Calculates area of visible (non-transparent) regions from alpha-enabled TIFF imagery.
  - Calculates total area from Esri Shapefile polygons (ROI).
  - Supports units in hectares (ha) or square meters (m²).

- **🌍 Worldwide Geographic Support**
  - **Dynamic Coordinate System Selection**: Automatically determines the optimal UTM coordinate system for any geographic location.
  - **Global Coverage**: Supports all UTM zones (1-60) for both Northern and Southern hemispheres.
  - **Accurate Projections**: Uses local UTM projections to minimize distortion and ensure precise area calculations.
  - **Fallback Protection**: Gracefully falls back to Web Mercator if UTM zone calculation fails.
  - **Perfect for International Use**: Works seamlessly with data from any region worldwide.

- **Map Visualization**
  - Downsampled TIFF preview with high-speed rendering.
  - Overlays two color-coded semi-transparent polygons:
    - Red: TIFF mask extent
    - Blue: ROI from shapefile
  - Clean map layout for screenshots or reporting (no axis/grid clutter).
  - Dark theme compatible with optimized colors for visibility.

- **High-Resolution Export**
  - Export high-DPI PNG images.
  - Optional area overlays (TIFF and ROI polygons).
  - Optional measurement overlays (width, height, and area information).
  - Professional-quality outputs suitable for reports and presentations.

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
shapely>=2.0.0         # Geometric operations
pyproj>=3.0.0          # Coordinate reference system handling
Pillow>=9.0.0          # Image processing for high-quality exports
```

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Jakub-Espandr/UAVAreaCalc.git
cd UAVAreaCalc

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

```

---

## 🛠️ Usage

1. Launch the app with `python main.py`
2. Click **"Browse GeoTIFF"** and select an alpha-enabled `.tif`
3. Click **"Browse Shapefile"** to add your ROI
4. Click **"Calculate Areas"** to process the data
5. The map will display both overlays with measurements
6. Toggle between hectares or square meters in the unit panel
7. **Export High-Resolution Images:**
   - Select export format (PNG or TIFF)
   - Choose DPI resolution (72-1200 DPI)
   - Enable/disable area overlays and measurements
   - Click **"Export High-Resolution Image"** to save

---

## 🌐 Coordinate System Intelligence

UAV AreaCalc automatically handles coordinate systems for optimal accuracy:

### **How It Works**
- **Automatic Detection**: Analyzes the geographic center of your data
- **UTM Zone Calculation**: Determines the optimal UTM zone using longitude/latitude
- **Hemisphere Detection**: Selects Northern (EPSG:326xx) or Southern (EPSG:327xx) projection
- **Local Optimization**: Uses the most accurate projection for your specific location

### **Supported Regions**
- **Europe**: Zones 28-38 (Czech Republic: 33N, Albania: 34N, Greece: 34N)
- **North America**: Zones 10-19 (New York: 17N, California: 11N)
- **Asia**: Zones 42-58 (Beijing: 51N, Tokyo: 54N)
- **Australia**: Zones 49-56 (Sydney: 55S, Melbourne: 55S)
- **South America**: Zones 18-25 (São Paulo: 22S, Buenos Aires: 21S)
- **Africa**: Zones 28-39 (Cape Town: 36S, Cairo: 36N)

### **Accuracy Benefits**
- **Minimal Distortion**: Local UTM projections provide the most accurate area calculations
- **Consistent Results**: Same data processed anywhere in the world yields identical results
- **Professional Standards**: Matches the accuracy of commercial GIS software

---

## 📁 Project Structure

```
UAVAreaCalc/
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

See the full [LICENSE](https://github.com/Jakub-Espandr/UAVAreaCalc/blob/main/LICENSE) for terms.

---

## 🙏 Acknowledgments

- Built using open-source geospatial libraries: Rasterio, GeoPandas, PySide6, Pillow, Matplotlib.