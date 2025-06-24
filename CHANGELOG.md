# Changelog


## [0.1.4] - 2025-06-24

### Changed

-   **Measurement Box Styling Improvements**:
    -   Changed measurement lines and rectangle from white to black for better visibility against white TIFF backgrounds.
    -   Optimalized measurement line width for improved prominence.
    -   Enhanced text styling with bold black text on white background and rounded bounding boxes.
    -   Applied consistent styling across both preview and export visualizations.

---

## [0.1.3] - 2025-06-23

### Added

-   **High-Resolution Export Functionality**:
    -   Added export options for high-DPI PNG.
    -   Optional area overlays (TIFF and ROI polygons) for export customization.
    -   Optional measurement overlays (width, height, and area information) for comprehensive documentation.
    -   Professional-quality outputs suitable for reports, presentations, and technical documentation.
-   **Enhanced Export Controls**:
    -   Checkbox controls for toggling area overlays and measurement displays.
    -   Export button that enables only after successful area calculations.
-   **Improved Image Quality**:
    -   Enhanced text rendering with better contrast and readability.
    -   Optimized figure sizing and layout for high-quality output.

### Technical

-   **Export Architecture**:
    -   Implemented `create_high_res_export()` method for dedicated export rendering.
    -   Added export-related event handlers for UI controls.
    -   Enhanced matplotlib figure management with proper cleanup.
    -   Added Pillow dependency for improved image processing capabilities.
-   **UI Enhancements**:
    -   Added export controls group to the left panel with organized layout.
    -   Integrated export button state management with calculation workflow.
    -   Added proper error handling and user feedback for export operations.

---

## [0.1.2] - 2025-06-22

### Fixed

-   **Critical Coordinate System Bug**: 
    -   Fixed major bug where ROI overlay appeared incorrectly positioned for data from different geographic regions.
    -   **Czech Republic data**: ROI overlay appeared correctly aligned with TIFF.
    -   **Albania data**: ROI overlay appeared distant and small, as if from a different location 100km away.
    -   **Root Cause**: Application was using hardcoded EPSG:32633 (UTM Zone 33N) for all regions.
    -   **Solution**: Implemented dynamic coordinate system selection using `get_optimal_utm_crs()` function.
    -   **Impact**: Now works correctly for worldwide regions with automatic UTM zone selection.
-   **Threading Issues**: 
    -   Fixed QObject threading warnings that appeared in terminal output.
    -   Properly managed worker object lifecycle to prevent threading conflicts.
    -   Improved application stability and reduced console noise.

### Added

-   **Worldwide Geographic Support**: 
    -   Application now automatically selects the optimal UTM coordinate system for any geographic location.
    -   Supports all UTM zones (1-60) for both Northern and Southern hemispheres.
    -   Fallback to Web Mercator (EPSG:3857) if UTM zone calculation fails.

### Technical

-   **Coordinate System Logic**: 
    -   Replaced hardcoded `epsg=32633` with dynamic `get_optimal_utm_crs()` calls.
    -   Ensured consistent coordinate system usage between TIFF and ROI processing.
    -   Added proper coordinate system handling in both worker thread and visualization.
-   **Code Quality**: 
    -   Fixed worker thread cleanup to prevent memory leaks.
    -   Improved signal/slot connections for better Qt integration.

---

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