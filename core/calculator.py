import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
from pyproj import CRS
from pyproj.exceptions import CRSError
import numpy as np

def get_optimal_utm_crs(gdf):
    """Determines the optimal local UTM CRS for a given GeoDataFrame to minimize distortion."""
    # Ensure the GeoDataFrame is in a geographic CRS (like WGS84) to get lat/lon bounds
    gdf_geo = gdf.to_crs(epsg=4326)
    
    # Find the center of the data's geographic bounds
    bounds = gdf_geo.total_bounds
    centroid_lon = (bounds[0] + bounds[2]) / 2
    
    # Calculate the UTM zone from the longitude
    utm_zone = int((centroid_lon + 180) / 6) + 1
    
    # Determine if the location is in the northern or southern hemisphere
    # We can check the mean latitude of the geometry
    centroid_lat = (bounds[1] + bounds[3]) / 2
    
    # Construct the EPSG code. North is 326xx, South is 327xx.
    if centroid_lat >= 0:
        epsg_code = 32600 + utm_zone
    else:
        epsg_code = 32700 + utm_zone
        
    try:
        # Verify that the calculated EPSG code is valid
        return CRS.from_epsg(epsg_code)
    except CRSError:
        # If the dynamic zone calculation fails for any reason, fall back to a global projected CRS.
        # This is a safety net, but Web Mercator is less accurate for area calculations.
        print(f"Warning: Could not determine local UTM zone {utm_zone}. Falling back to EPSG:3857.")
        return CRS.from_epsg(3857)

def calculate_tiff_area_m2(tiff_path):
    """Calculates the area of the opaque region of a TIFF file in square meters."""
    with rasterio.open(tiff_path) as src:
        if src.count < 4:
            raise ValueError("TIFF file must have an alpha channel (4 channels required).")
        
        alpha = src.read(4)
        mask = alpha > 0
        
        results = ({'geometry': shape(geom)} for geom, val in shapes(alpha, mask=mask, transform=src.transform) if val > 0)
        geoms = list(results)
        
        if not geoms:
            raise ValueError("No opaque areas with value > 0 found in the TIFF file.")
            
        gdf = gpd.GeoDataFrame(geometry=[g["geometry"] for g in geoms], crs=src.crs)
        
        # Dissolve all generated shapes into a single feature to ensure total area is calculated.
        gdf_dissolved = gdf.dissolve()

        # Determine and reproject to the optimal local projection for this data
        optimal_crs = get_optimal_utm_crs(gdf_dissolved)
        gdf_metric = gdf_dissolved.to_crs(optimal_crs)
        
        # Return the area of the single, unified geometry.
        return gdf_metric.area.iloc[0]

def calculate_roi_area_m2(shp_path):
    """Calculates the total area of a shapefile's features in square meters."""
    roi = gpd.read_file(shp_path)
    
    # Determine and reproject to the optimal local projection for this data
    optimal_crs = get_optimal_utm_crs(roi)
    roi_metric = roi.to_crs(optimal_crs)
    
    # First, merge all features into a single geometry to handle multi-part or overlapping shapes correctly.
    unified_geometry = roi_metric.unary_union
    
    # Then, calculate the area of the single, unified shape.
    return unified_geometry.area

def calculate_roi_dimensions_m(shp_path):
    """
    Calculates the width and height of the minimum rotated rectangle of a shapefile.
    Returns the shorter side as width, the longer side as height, and the rectangle geometry.
    """
    roi = gpd.read_file(shp_path)

    # Determine and reproject to the optimal local projection for this data
    optimal_crs = get_optimal_utm_crs(roi)
    roi_metric = roi.to_crs(optimal_crs)
    
    # Dissolve all features into a single geometry to properly calculate the overall rectangle
    unified_geometry = roi_metric.unary_union
    
    # Get the minimum rotated rectangle, which is the smallest possible bounding box at any angle
    rotated_rect = unified_geometry.minimum_rotated_rectangle
    
    # Get the coordinates of the rectangle's corners
    x, y = rotated_rect.exterior.coords.xy
    
    # Calculate the length of the first two unique sides of the rectangle
    side1_length = ((x[1] - x[0])**2 + (y[1] - y[0])**2)**0.5
    side2_length = ((x[2] - x[1])**2 + (y[2] - y[1])**2)**0.5
    
    # Assign width and height based on length
    width = min(side1_length, side2_length)
    height = max(side1_length, side2_length)
    
    return width, height, rotated_rect 