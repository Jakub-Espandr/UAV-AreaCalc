# Changelog


## [0.1.1] - 2025-06-22

### Fixed

-   **Critical ROI Area Calculation Bug**: 
    -   Fixed major bug where ROI area calculation was summing areas of all features instead of calculating unified geometry area.
    -   Implemented `unary_union` to properly dissolve multiple features before area calculation.
    -   Results now match professional GIS software (ArcGIS Pro) with high accuracy.
-   **TIFF Area Calculation Accuracy**: 
    -   Fixed similar bug in TIFF area calculation where individual polygon areas were summed incorrectly.
    -   Now properly dissolves all non-transparent regions into a single feature before measuring total area.
-   **Projection Accuracy**: 
    -   Replaced hardcoded UTM projection with dynamic local UTM projection determination.
    -   System now automatically selects optimal UTM zone based on data's geographic center for maximum accuracy.

### Added

-   **ROI Dimension Measurements**: 
    -   Added calculation and display of ROI width and height using minimum rotated rectangle algorithm.
    -   Dimensions are displayed on the visualization with measurement lines and labels.
    -   Provides comprehensive spatial analysis beyond just area calculations.

### Changed

-   **Reduced macOS Warnings**: 
    -   Added environment variable settings to suppress common Qt threading warnings on macOS.
    -   Improved application startup experience with cleaner console output.

### Technical

-   **Code Refactoring**: 
    -   Simplified the `update_display()` method.
    -   Enhanced dimension drawing logic with intelligent text positioning.
    -   Added macOS-specific environment variables for better Qt integration.

---

## [0.1.0] - 2025-06-22

### Added

-   **Initial Release** of the UAV Area Calculator application.
-   **Core Area Calculation**:
    -   Calculates the area of non-transparent regions from GeoTIFF files with an alpha channel.
    -   Calculates the total area from Esri Shapefiles.
-   **Graphical User Interface (GUI)**:
    -   Built with PySide6 for a modern, cross-platform experience.
    -   Split-view layout with controls on the left and a map visualization on the right.
    -   Responsive design with a configurable minimum window size.
-   **File Selection**:
    -   User-friendly "Browse" dialogs for selecting TIFF and Shapefile (`.shp`) inputs.
-   **Unit Conversion**:
    -   Display calculated areas in either Hectares (ha) or Square Meters (m²).
    -   Radio buttons allow for instant unit switching.
-   **Map Visualization**:
    -   Displays the source GeoTIFF as a basemap.
    -   Overlays the calculated TIFF area (in red) and Shapefile ROI (in blue) as semi-transparent polygons.
    -   Minimalist map design with no axes, labels, or borders for a clean, presentation-ready output.
-   **Custom Theming**:
    -   Loads and applies custom `fccTYPO` fonts throughout the application.
    -   Sets a custom application icon (`.icns` for macOS, `.png` for Windows/Linux).
    -   Color-coded result labels in the UI to match the map visualization colors.
-   **Structured Codebase**:
    -   Project code is organized into `ui`, `core`, and `utils` modules for improved maintainability and scalability. 