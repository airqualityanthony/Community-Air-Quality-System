
from osdatahub import FeaturesAPI, Extent, NGD
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
import mapclassify as mc
from shapely.geometry import Point
import os
import numpy as np
from convertbng.util import convert_bng, convert_lonlat

key = os.environ.get('OS_API_KEY')
crs = "EPSG:27700"

def OSparam_feature(u,v,rad,product,key,clip):
    extent = Extent.from_radius((u,v), rad, "EPSG:27700")
    features = FeaturesAPI(key, product, extent)
    results = features.query(limit=500)
    if len(results['features']) == 0:
        out = 0
    TA_gdf = gpd.GeoDataFrame.from_features(results['features'])

    if clip == True:
        patch = Point(u,v).buffer(rad)
        d = {'col1': ['name1'], 'geometry': [patch]}
        patch_df = gpd.GeoDataFrame(d, crs="EPSG:27700")
        TA_gdf = TA_gdf.clip(patch)
    try:
        gd = (TA_gdf['Theme'] == 'Buildings') & (~np.isnan(TA_gdf['RelH2']))
        out = np.average(TA_gdf['RelH2'][gd], weights=TA_gdf['Shape_Area'][gd])
    except TypeError:
        out = 0
    return out, TA_gdf

def building_height_radius(X, Y, radius,product,key, clip):
    area, TA = OSparam_feature(X, Y, radius, product,key, clip)
    TA = TA.set_crs(27700)
    TA_ll = TA.to_crs(4326)
    lon, lat = convert_lonlat(X,Y)
    map = TA_ll.explore('RelH2') ## colour by height
    folium.Marker([lat[0], lon[0]],popup=[lat[0],lon[0]]).add_to(map)
    return map
    