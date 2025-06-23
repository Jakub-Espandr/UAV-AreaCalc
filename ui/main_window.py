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
    QGroupBox, QProgressBar, QSpinBox, QComboBox, QCheckBox
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
        self.setMinimumSize(1000, 500)
        if app_icon:
            self.setWindowIcon(app_icon)

        # Data variables
        self.tiff_area_m2 = 0
        self.roi_area_m2 = 0
        self.roi_width_m = 0
        self.roi_height_m = 0
        self.roi_rotated_rect = None
        
        # Export variables
        self.export_dpi = 600  # Always 600 DPI
        self.export_format = "PNG"  # Always PNG
        self.export_show_measurements = True
        self.export_show_areas = True

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
        
        # Export controls
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout()
        
        # Overlay options
        self.show_measurements_check = QCheckBox("Show measurements")
        self.show_measurements_check.setChecked(True)
        self.show_measurements_check.toggled.connect(self.on_show_measurements_changed)
        export_layout.addWidget(self.show_measurements_check)
        
        self.show_areas_check = QCheckBox("Show area overlays")
        self.show_areas_check.setChecked(True)
        self.show_areas_check.toggled.connect(self.on_show_areas_changed)
        export_layout.addWidget(self.show_areas_check)
        
        # Export button
        self.export_button = QPushButton("Export High-Resolution PNG")
        self.export_button.clicked.connect(self.export_high_res_image)
        self.export_button.setEnabled(False)  # Disabled until calculations are complete
        export_layout.addWidget(self.export_button)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
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
        
        # Enable export button now that we have results
        self.export_button.setEnabled(True)
        
        self.status_label.setText("Processing complete. Ready.")
        self.cleanup_after_run()

    def cleanup_after_run(self):
        """Re-enables the button and schedules the progress bar to hide."""
        self.calc_button.setEnabled(True)
        def hide_and_reset_bar():
            self.progress_bar.hide()
            self.progress_bar.setStyleSheet("")
        QTimer.singleShot(1500, hide_and_reset_bar)

    def on_show_measurements_changed(self, checked):
        """Handle show measurements checkbox change."""
        self.export_show_measurements = checked

    def on_show_areas_changed(self, checked):
        """Handle show areas checkbox change."""
        self.export_show_areas = checked

    def export_high_res_image(self):
        """Export a high-resolution PNG image with overlays and measurements in a background thread."""
        if not self.tiff_path_edit.text() or not self.shp_path_edit.text():
            self.status_label.setText("Error: Please load data first.")
            return
            
        if self.tiff_area_m2 <= 0 or self.roi_area_m2 <= 0:
            self.status_label.setText("Error: Please calculate areas first.")
            return

        # Always use PNG
        file_filter = "PNG Files (*.png)"
        default_name = f"uav_area_analysis.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save High-Resolution PNG", 
            default_name, 
            file_filter
        )
        
        if not file_path:
            return

        self.status_label.setText("Exporting, please wait...")
        self.export_button.setEnabled(False)
        QApplication.processEvents()

        # Set up export worker and thread
        self.export_thread = QThread()
        self.export_worker = ExportWorker(file_path, self.create_high_res_export)
        self.export_worker.moveToThread(self.export_thread)
        self.export_thread.started.connect(self.export_worker.run)
        self.export_worker.finished.connect(self.handle_export_finished)
        self.export_worker.error.connect(self.handle_export_error)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.error.connect(self.export_thread.quit)
        self.export_thread.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        self.export_thread.start()

    def handle_export_finished(self, file_path):
        self.status_label.setText(f"Export complete: {os.path.basename(file_path)}")
        self.export_button.setEnabled(True)
        QTimer.singleShot(2000, lambda: self.status_label.setText("Ready"))

    def handle_export_error(self, error_msg):
        self.status_label.setText(f"Export error: {error_msg}")
        self.export_button.setEnabled(True)
        QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))

    def create_high_res_export(self, file_path):
        """Create a high-resolution export with overlays and measurements."""
        # Create a new figure with high DPI and extra space for info
        fig, (ax, ax_info) = plt.subplots(2, 1, figsize=(12, 10), dpi=self.export_dpi, 
                                         gridspec_kw={'height_ratios': [15, 0.5]})
        
        tiff_path = self.tiff_path_edit.text()
        shp_path = self.shp_path_edit.text()

        try:
            # Display high-resolution TIFF
            with rasterio.open(tiff_path) as src:
                # Use higher resolution for export
                scale = 10  # Less downsampling for higher quality
                out_shape = (src.count, int(src.height//scale), int(src.width//scale))
                image = src.read(out_shape=out_shape, resampling=Resampling.bilinear)
                transform = src.transform * src.transform.scale((src.width / image.shape[-1]), (src.height / image.shape[-2]))
                rasterio.plot.show(image, transform=transform, ax=ax)
            
            # Plot TIFF polygon overlay if enabled
            if self.export_show_areas:
                with rasterio.open(tiff_path) as src:
                    alpha = src.read(4)
                    mask = alpha > 0
                    results = ({'geometry': shape(geom)} for geom, val in shapes(alpha, mask=mask, transform=src.transform) if val > 0)
                    geoms = list(results)
                    gdf = gpd.GeoDataFrame(geometry=[g["geometry"] for g in geoms], crs=src.crs).dissolve()
                    
                    optimal_crs = get_optimal_utm_crs(gdf)
                    gdf_optimal = gdf.to_crs(optimal_crs)
                    gdf_optimal.plot(ax=ax, facecolor='red', edgecolor='red', alpha=0.3, linewidth=2)
            
            # Plot ROI polygon and measurements if enabled
            if self.export_show_areas or self.export_show_measurements:
                roi = gpd.read_file(shp_path)
                optimal_crs = get_optimal_utm_crs(roi)
                roi_optimal = roi.to_crs(optimal_crs)
                
                if self.export_show_areas:
                    roi_optimal.plot(ax=ax, facecolor='#4FC3F7', edgecolor='#29B6F6', alpha=0.6, linewidth=2)
                
                # Draw measurements if enabled
                if self.export_show_measurements and self.roi_rotated_rect:
                    # Draw the minimum rotated rectangle
                    ax.plot(*self.roi_rotated_rect.exterior.xy, color='white', linestyle='--', linewidth=2)
                    
                    # Get the coordinates of the rectangle's corners
                    x, y = self.roi_rotated_rect.exterior.coords.xy
                    
                    # Function to draw a dimension line with text
                    def draw_dimension(coords, text):
                        x1, y1, x2, y2 = coords
                        mid_x = (x1 + x2) / 2
                        mid_y = (y1 + y2) / 2
                        ax.plot([x1, x2], [y1, y2], color='white', linestyle='-', linewidth=3)
                        
                        # Determine orientation to place text correctly
                        is_horizontal = abs(x2 - x1) > abs(y2 - y1)
                        
                        ha = 'center' if is_horizontal else 'left'
                        va = 'bottom' if is_horizontal else 'center'
                        
                        ax.text(mid_x, mid_y, f' {text} ', ha=ha, va=va, rotation=0,
                                 fontsize=12, color='white', backgroundcolor=(0,0,0,0.8), 
                                 weight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))

                    # Determine which side is width vs height
                    side1_len = np.sqrt((x[1] - x[0])**2 + (y[1] - y[0])**2)
                    
                    if np.isclose(side1_len, self.roi_width_m):
                        width_coords = (x[0], y[0], x[1], y[1])
                        height_coords = (x[1], y[1], x[2], y[2])
                    else:
                        width_coords = (x[1], y[1], x[2], y[2])
                        height_coords = (x[0], y[0], x[1], y[1])

                    # Draw width and height measurements
                    draw_dimension(width_coords, f'{self.roi_width_m:.2f} m')
                    draw_dimension(height_coords, f'{self.roi_height_m:.2f} m')

            # Set up the map area
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.axis('equal')
            
            # Create information area below the map
            ax_info.set_xticks([])
            ax_info.set_yticks([])
            for spine in ax_info.spines.values():
                spine.set_visible(False)
            ax_info.set_facecolor('white')
            fig.patch.set_facecolor('white')  # Ensure figure background is white
            
            # Calculate area values for display
            unit_text = "ha" if self.ha_radio.isChecked() else "m²"
            tiff_area_display = self.tiff_area_m2 / 10000 if self.ha_radio.isChecked() else self.tiff_area_m2
            roi_area_display = self.roi_area_m2 / 10000 if self.ha_radio.isChecked() else self.roi_area_m2
            
            # Compose the info line with colored values using multiple text elements
            tiff_label = f"TIFF Area: "
            tiff_value = f"{tiff_area_display:.4f} {unit_text}"
            roi_label = f" | ROI Area: "
            roi_value = f"{roi_area_display:.4f} {unit_text}"

            # Calculate total width for centering
            dummy = ax_info.text(0.5, 0.5, tiff_label + tiff_value + roi_label + roi_value, fontsize=16, weight='bold', ha='center', va='center', color='black', alpha=0)
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            bbox = dummy.get_window_extent(renderer=renderer)
            dummy.remove()
            width = bbox.width / fig.dpi / fig.get_figwidth()
            x = 0.5 - width / 2
            y = 0.5
            def text_width(s, **kwargs):
                t = ax_info.text(0, 0, s, fontsize=16, weight='bold', ha='left', va='center', color='black', alpha=0, **kwargs)
                fig.canvas.draw()
                w = t.get_window_extent(renderer=renderer).width / fig.dpi / fig.get_figwidth()
                t.remove()
                return w
            tw1 = text_width(tiff_label)
            tw2 = text_width(tiff_value)
            tw3 = text_width(roi_label)
            tw4 = text_width(roi_value)
            ax_info.text(x, y, tiff_label, fontsize=16, weight='bold', ha='left', va='center', color='black', zorder=2, transform=ax_info.transAxes)
            x += tw1
            ax_info.text(x, y, tiff_value, fontsize=16, weight='bold', ha='left', va='center', color='red', zorder=2, transform=ax_info.transAxes)
            x += tw2
            ax_info.text(x, y, roi_label, fontsize=16, weight='bold', ha='left', va='center', color='black', zorder=2, transform=ax_info.transAxes)
            x += tw3
            ax_info.text(x, y, roi_value, fontsize=16, weight='bold', ha='left', va='center', color='#4FC3F7', zorder=2, transform=ax_info.transAxes)

            fig.tight_layout()
            
            # Save with high quality settings
            fig.savefig(file_path, dpi=self.export_dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', transparent=False, pil_kwargs={"quality": 100})
            
            plt.close(fig)
            
        except Exception as e:
            plt.close(fig)
            raise e

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

class ExportWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, file_path, create_export_func):
        super().__init__()
        self.file_path = file_path
        self.create_export_func = create_export_func

    def run(self):
        try:
            self.create_export_func(self.file_path)
            self.finished.emit(self.file_path)
        except Exception as e:
            self.error.emit(str(e)) 