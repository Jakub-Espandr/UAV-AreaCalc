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
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QFrame, QRadioButton,
    QGroupBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Import the refactored calculation logic
from core.calculator import calculate_tiff_area_m2, calculate_roi_area_m2

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
        calc_button = QPushButton("Calculate Areas")
        calc_button.clicked.connect(self.calculate_areas)
        layout.addWidget(calc_button)
        
        # Results frame
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        self.tiff_area_label = QLabel("TIFF Area: Not calculated")
        self.tiff_area_label.setStyleSheet("color: red;")
        self.roi_area_label = QLabel("ROI Area: Not calculated")
        self.roi_area_label.setStyleSheet("color: blue;")
        results_layout.addWidget(self.tiff_area_label)
        results_layout.addWidget(self.roi_area_label)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
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

    def calculate_areas(self):
        tiff_path = self.tiff_path_edit.text()
        shp_path = self.shp_path_edit.text()

        if not tiff_path or not shp_path:
            print("Error: Please select both TIFF and Shapefile")
            return
            
        try:
            self.tiff_area_m2 = calculate_tiff_area_m2(tiff_path)
            self.roi_area_m2 = calculate_roi_area_m2(shp_path)
            
            self.update_display()
            self.update_visualization()
            
        except Exception as e:
            print(f"Error calculating areas: {e}")

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
                gdf.to_crs(epsg=32633).plot(ax=self.ax, facecolor='red', edgecolor='red', alpha=0.3, linewidth=2)
            
            # Plot ROI polygon
            gpd.read_file(shp_path).to_crs(epsg=32633).plot(ax=self.ax, facecolor='blue', edgecolor='blue', alpha=0.3, linewidth=2)

            plt.axis('equal')
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating visualization: {e}") 