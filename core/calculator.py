import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd

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
            
        gdf = gpd.GeoDataFrame(geometry=[g["geometry"] for g in geoms], crs=src.crs).dissolve()
        
        # Reproject to a metric CRS (UTM Zone 33N is common for Europe) to get area in meters
        gdf_metric = gdf.to_crs(epsg=32633)
        
        return gdf_metric.area.iloc[0]

def calculate_roi_area_m2(shp_path):
    """Calculates the total area of a shapefile's features in square meters."""
    roi = gpd.read_file(shp_path)
    
    # Reproject to a metric CRS to get area in meters
    roi_metric = roi.to_crs(epsg=32633)
    
    return roi_metric.area.sum() 