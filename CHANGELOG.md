# Changelog


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