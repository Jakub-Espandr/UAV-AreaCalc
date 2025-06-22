import sys
import os
import rasterio
import rasterio.plot
from rasterio.enums import Resampling
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QFrame, QRadioButton,
    QGroupBox, QProgressBar
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QThread

# Import the refactored calculation logic
from core.calculator import get_optimal_utm_crs

class CalculationWorker(QObject):
    """
    A worker that runs the long calculations in a separate thread to keep the UI responsive.
    """
    progress_update = Signal(int, str)
    calculation_finished = Signal(dict)
    calculation_error = Signal(str)

    def __init__(self, tiff_path, shp_path):
        super().__init__()
        self.tiff_path = tiff_path
        self.shp_path = shp_path

    def run(self):
        """The main work of the thread, broken into granular steps."""
        try:
            # --- TIFF Processing ---
            self.progress_update.emit(5, "Processing (1/8): Reading TIFF file...")
            with rasterio.open(self.tiff_path) as src:
                if src.count < 4:
                    raise ValueError("TIFF file must have an alpha channel.")
                
                alpha = src.read(4)
                mask = alpha > 0
                crs = src.crs

            self.progress_update.emit(15, "Processing (2/8): Extracting TIFF geometry...")
            results_gen = ({'geometry': shape(geom)} for geom, val in shapes(alpha, mask=mask, transform=src.transform) if val > 0)
            geoms = list(results_gen)
            if not geoms:
                raise ValueError("No opaque areas found in TIFF.")

            self.progress_update.emit(25, "Processing (3/8): Unifying TIFF shapes...")
            gdf = gpd.GeoDataFrame(geometry=[g["geometry"] for g in geoms], crs=crs)
            gdf_dissolved = gdf.dissolve()

            self.progress_update.emit(35, "Processing (4/8): Calculating TIFF area...")
            optimal_crs = get_optimal_utm_crs(gdf_dissolved)
            gdf_metric = gdf_dissolved.to_crs(optimal_crs)
            tiff_area_m2 = gdf_metric.area.iloc[0]

            # --- ROI Processing ---
            self.progress_update.emit(45, "Processing (5/8): Reading Shapefile...")
            roi = gpd.read_file(self.shp_path)
            
            # Use the same optimal coordinate system as the TIFF to ensure proper alignment
            roi_metric = roi.to_crs(optimal_crs)

            self.progress_update.emit(55, "Processing (6/8): Calculating ROI area...")
            unified_geometry = roi_metric.unary_union
            roi_area_m2 = unified_geometry.area

            self.progress_update.emit(65, "Processing (7/8): Calculating ROI dimensions...")
            rotated_rect = unified_geometry.minimum_rotated_rectangle
            x, y = rotated_rect.exterior.coords.xy
            side1_length = ((x[1] - x[0])**2 + (y[1] - y[0])**2)**0.5
            side2_length = ((x[2] - x[1])**2 + (y[2] - y[1])**2)**0.5
            roi_width_m = min(side1_length, side2_length)
            roi_height_m = max(side1_length, side2_length)

            # --- Finalize ---
            self.progress_update.emit(75, "Processing (8/8): Finalizing results...")
            results = {
                "tiff_area_m2": tiff_area_m2,
                "roi_area_m2": roi_area_m2,
                "roi_width_m": roi_width_m,
                "roi_height_m": roi_height_m,
                "roi_rotated_rect": rotated_rect,
            }
            self.calculation_finished.emit(results)
        except Exception as e:
            self.calculation_error.emit(str(e))


class UAVAreaCalculator(QMainWindow):
    def __init__(self, app_icon=None):
        super().__init__()
        self.setWindowTitle("UAV Area Calculator")
        self.setGeometry(100, 100, 1000, 500)
        self.setMinimumSize(800, 400)
        if app_icon:
            self.setWindowIcon(app_icon)

        # Data variables
        self.tiff_area_m2 = 0
        self.roi_area_m2 = 0
        self.roi_width_m = 0
        self.roi_height_m = 0
        self.roi_rotated_rect = None

        self.setup_ui()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Left panel for settings
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.NoFrame)
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(400)

        # Right panel for visualization
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.NoFrame)
        right_panel_layout = QVBoxLayout(right_panel)
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1) # Make right panel expand

        self.setup_left_panel(left_panel_layout)
        self.setup_right_panel(right_panel_layout)

    def setup_left_panel(self, layout):
        # TIFF file selection
        self.tiff_path_edit = QLineEdit()
        self.tiff_path_edit.setPlaceholderText("Path to TIFF file...")
        tiff_button = QPushButton("Browse")
        tiff_button.clicked.connect(self.browse_tiff)
        
        tiff_layout = QHBoxLayout()
        tiff_layout.addWidget(QLabel("TIFF File:"))
        tiff_layout.addWidget(self.tiff_path_edit)
        tiff_layout.addWidget(tiff_button)
        layout.addLayout(tiff_layout)
        
        # Shapefile selection
        self.shp_path_edit = QLineEdit()
        self.shp_path_edit.setPlaceholderText("Path to Shapefile...")
        shp_button = QPushButton("Browse")
        shp_button.clicked.connect(self.browse_shp)
        
        shp_layout = QHBoxLayout()
        shp_layout.addWidget(QLabel("Shapefile:"))
        shp_layout.addWidget(self.shp_path_edit)
        shp_layout.addWidget(shp_button)
        layout.addLayout(shp_layout)
        
        # Unit selection
        unit_group = QGroupBox("Unit")
        unit_layout = QHBoxLayout()
        self.ha_radio = QRadioButton("Hectares (ha)")
        self.ha_radio.setChecked(True)
        self.m2_radio = QRadioButton("Square meters (m²)")
        self.ha_radio.toggled.connect(self.update_display)
        unit_layout.addWidget(self.ha_radio)
        unit_layout.addWidget(self.m2_radio)
        unit_group.setLayout(unit_layout)
        layout.addWidget(unit_group)
        
        # Calculate button
        self.calc_button = QPushButton("Calculate Areas")
        self.calc_button.clicked.connect(self.start_calculations)
        layout.addWidget(self.calc_button)
        
        # Results frame
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.tiff_area_label = QLabel("TIFF Area: Not calculated")
        self.tiff_area_label.setStyleSheet("color: red;")
        self.roi_area_label = QLabel("ROI Area: Not calculated")
        self.roi_area_label.setStyleSheet("color: #4FC3F7;")  # Light blue for dark theme visibility
        results_layout.addWidget(self.tiff_area_label)
        results_layout.addWidget(self.roi_area_label)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Status Label and Progress Bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; padding-top: 10px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        layout.addStretch() # Pushes everything to the top

    def setup_right_panel(self, layout):
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        self.update_visualization() # Initial placeholder

    def browse_tiff(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select TIFF file", "", "TIFF Files (*.tif *.tiff)")
        if path:
            self.tiff_path_edit.setText(path)
            
    def browse_shp(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Shapefile", "", "Shapefiles (*.shp)")
        if path:
            self.shp_path_edit.setText(path)

    def update_display(self):
        if self.tiff_area_m2 > 0 and self.roi_area_m2 > 0:
            if self.ha_radio.isChecked():
                self.tiff_area_label.setText(f"TIFF Area: {self.tiff_area_m2 / 10000:.6f} ha")
                self.roi_area_label.setText(f"ROI Area: {self.roi_area_m2 / 10000:.6f} ha")
            else:
                self.tiff_area_label.setText(f"TIFF Area: {self.tiff_area_m2:.2f} m²")
                self.roi_area_label.setText(f"ROI Area: {self.roi_area_m2:.2f} m²")

    def start_calculations(self):
        tiff_path = self.tiff_path_edit.text()
        shp_path = self.shp_path_edit.text()

        if not tiff_path or not shp_path:
            self.status_label.setText("Error: Please select both files first.")
            return
            
        # --- UI Setup Before Threading ---
        self.calc_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("") # Reset style
        self.status_label.setText("Starting processing...")
        self.progress_bar.show()

        # --- Worker Thread Setup ---
        self.thread = QThread()
        self.worker = CalculationWorker(tiff_path, shp_path)
        self.worker.moveToThread(self.thread)

        # --- Signal / Slot Connections ---
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.calculation_finished.connect(self.handle_results)
        self.worker.calculation_error.connect(self.handle_error)

        # --- Cleanup ---
        self.worker.calculation_finished.connect(self.thread.quit)
        self.worker.calculation_error.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def update_progress(self, value, text):
        """Slot to receive progress updates from the worker."""
        self.progress_bar.setValue(value)
        self.status_label.setText(text)

    def handle_error(self, error_msg):
        """Slot to handle errors from the worker."""
        error_message = f"Error: {error_msg[:100]}..." if len(error_msg) > 100 else f"Error: {error_msg}"
        self.status_label.setText(error_message)
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        print(f"Error during calculation: {error_msg}")
        self.cleanup_after_run()

    def handle_results(self, results):
        """Slot to handle the successful results from the worker."""
        self.tiff_area_m2 = results["tiff_area_m2"]
        self.roi_area_m2 = results["roi_area_m2"]
        self.roi_width_m = results["roi_width_m"]
        self.roi_height_m = results["roi_height_m"]
        self.roi_rotated_rect = results["roi_rotated_rect"]
        
        self.update_display()
        
        self.update_progress(85, "Rendering visualization...")
        self.update_visualization()
        self.progress_bar.setValue(100)
        
        self.status_label.setText("Processing complete. Ready.")
        self.cleanup_after_run()

    def cleanup_after_run(self):
        """Re-enables the button and schedules the progress bar to hide."""
        self.calc_button.setEnabled(True)
        def hide_and_reset_bar():
            self.progress_bar.hide()
            self.progress_bar.setStyleSheet("")
        QTimer.singleShot(1500, hide_and_reset_bar)

    def update_visualization(self):
        self.ax.clear()
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        tiff_path = self.tiff_path_edit.text()
        shp_path = self.shp_path_edit.text()

        if not tiff_path or not shp_path:
            self.ax.text(0.5, 0.5, "Load data to see visualization", ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        try:
            # Display downsampled TIFF
            with rasterio.open(tiff_path) as src:
                scale = 30
                out_shape = (src.count, int(src.height//scale), int(src.width//scale))
                image = src.read(out_shape=out_shape, resampling=Resampling.bilinear)
                transform = src.transform * src.transform.scale((src.width / image.shape[-1]), (src.height / image.shape[-2]))
                rasterio.plot.show(image, transform=transform, ax=self.ax)
            
            # Plot TIFF polygon
            with rasterio.open(tiff_path) as src:
                alpha = src.read(4)
                mask = alpha > 0
                results = ({'geometry': shape(geom)} for geom, val in shapes(alpha, mask=mask, transform=src.transform) if val > 0)
                geoms = list(results)
                gdf = gpd.GeoDataFrame(geometry=[g["geometry"] for g in geoms], crs=src.crs).dissolve()
                
                # Use dynamic coordinate system selection instead of hardcoded EPSG:32633
                optimal_crs = get_optimal_utm_crs(gdf)
                gdf_optimal = gdf.to_crs(optimal_crs)
                gdf_optimal.plot(ax=self.ax, facecolor='red', edgecolor='red', alpha=0.3, linewidth=2)
            
            # Plot ROI polygon and its bounding box
            roi = gpd.read_file(shp_path)
            
            # Use the same optimal coordinate system for ROI to ensure proper alignment
            roi_optimal = roi.to_crs(optimal_crs)
            roi_optimal.plot(ax=self.ax, facecolor='#4FC3F7', edgecolor='#29B6F6', alpha=0.6, linewidth=2)  # Less transparent blue for better visibility
            
            # Draw the minimum rotated rectangle and dimension lines
            if self.roi_rotated_rect:
                # The rotated rectangle should already be in the optimal coordinate system
                # since it was calculated in the worker thread using the same CRS
                self.ax.plot(*self.roi_rotated_rect.exterior.xy, color='white', linestyle='--', linewidth=1)  # White dashed line for dark theme
                
                # Get the coordinates of the rectangle's corners
                x, y = self.roi_rotated_rect.exterior.coords.xy
                
                # Function to draw a dimension line with non-rotated text
                def draw_dimension(coords, text):
                    x1, y1, x2, y2 = coords
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    self.ax.plot([x1, x2], [y1, y2], color='white', linestyle='-', linewidth=2)  # White lines for dark theme
                    
                    # Determine orientation to place text correctly without rotation
                    is_horizontal = abs(x2 - x1) > abs(y2 - y1)
                    
                    ha = 'center' if is_horizontal else 'left'
                    va = 'bottom' if is_horizontal else 'center'
                    
                    self.ax.text(mid_x, mid_y, f' {text} ', ha=ha, va=va, rotation=0,
                                 fontsize=9, color='white', backgroundcolor=(0,0,0,0.8))  # White text with dark background

                # Determine which side is width vs height
                side1_len = np.sqrt((x[1] - x[0])**2 + (y[1] - y[0])**2)
                
                if np.isclose(side1_len, self.roi_width_m):
                    width_coords = (x[0], y[0], x[1], y[1])
                    height_coords = (x[1], y[1], x[2], y[2])
                else:
                    width_coords = (x[1], y[1], x[2], y[2])
                    height_coords = (x[0], y[0], x[1], y[1])

                # Draw width and height
                draw_dimension(width_coords, f'{self.roi_width_m:.2f} m')
                draw_dimension(height_coords, f'{self.roi_height_m:.2f} m')


            plt.axis('equal')
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating visualization: {e}") 