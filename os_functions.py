
from osdatahub import FeaturesAPI, Extent, NGD
import geopandas as gpd
import folium
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
    return TA_gdf

def OSparam_ngd(u,v,rad,product,key,clip):
    extent = Extent.from_radius((u,v), rad, "EPSG:27700")
    ngd = NGD(key, product)
    results = ngd.query(max_results=500, extent=extent)
    if len(results['features']) == 0:
        out = 0
    TA_gdf = gpd.GeoDataFrame.from_features(results['features'])
    return TA_gdf


def building_height_radius(X, Y, radius,product,key, clip):
    TA = OSparam_feature(X, Y, radius, product,key, clip)
    TA = TA.set_crs(27700)
    TA_ll = TA.to_crs(4326)
    lon, lat = convert_lonlat(X,Y)
    map = TA_ll.explore('RelH2') ## colour by height
    folium.Marker([lat[0], lon[0]],popup=[lat[0],lon[0]]).add_to(map)
    return TA_ll