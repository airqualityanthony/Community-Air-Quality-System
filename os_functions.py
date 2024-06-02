
from osdatahub import FeaturesAPI, Extent, NGD
import geopandas as gpd
import folium
from shapely.geometry import Point, LineString
import os
import numpy as np
from convertbng.util import convert_lonlat
import math


key = os.environ.get('OS_API_KEY')
crs = "EPSG:27700"

def OSparam_feature(u,v,rad,product,key,clip):
    extent = Extent.from_radius((u,v), rad, "EPSG:27700")
    features = FeaturesAPI(key, product, extent)
    results = features.query(limit=500)
    if len(results['features']) == 0:
        return ('No features found')
    else:
        TA_gdf = gpd.GeoDataFrame.from_features(results['features'])

    if clip == True:
        patch = Point(u,v).buffer(rad)
        TA_gdf = TA_gdf.clip(patch)

    TA = TA_gdf.set_crs(27700)
    return TA

def OSparam_ngd(u,v,rad,product,key,clip):
    extent = Extent.from_radius((u,v), rad, "EPSG:27700")
    ngd = NGD(key, product)
    results = ngd.query(max_results=500, extent=extent)
    if len(results['features']) == 0:
        return ('No features found')
    else: 
        TA_gdf = gpd.GeoDataFrame.from_features(results['features'])

    if clip == True:
        ll = convert_lonlat(u,v)
        patch = Point(ll[0],ll[1]).buffer(rad)
        TA_gdf = TA_gdf.clip(patch)

    TA = TA_gdf
    return TA


def building_height_radius(X, Y, radius,product,key, clip):
    TA = OSparam_feature(X, Y, radius, product,key, clip)
    TA = TA.set_crs(27700)
    TA_ll = TA.to_crs(4326)
    lon, lat = convert_lonlat(X,Y)
    map = TA_ll.explore('RelH2') ## colour by height
    folium.Marker([lat[0], lon[0]],popup=[lat[0],lon[0]]).add_to(map)
    return TA_ll


def calculate_bearing(pointA, pointB):
    lat1 = np.radians(pointA.y)
    lat2 = np.radians(pointB.y)
    diffLong = np.radians(pointB.x - pointA.x)
    x = np.sin(diffLong) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(diffLong))
    initial_bearing = np.arctan2(x, y)
    # Now we have the initial bearing but math.atan2() returns values from -π to + π 
    # so we need to normalize the result, converting it to a compass bearing as it 
    # should be in the range 0° to 360°
    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing


def calculate_bearing_linestring(line):
    if isinstance(line, LineString):
        pointA = line.coords[0]
        pointB = line.coords[-1]
    else:
        raise TypeError("Only LineString objects are supported")

    delta_x = pointB[0] - pointA[0]
    delta_y = pointB[1] - pointA[1]

    bearing = math.atan2(delta_y, delta_x)
    bearing = math.degrees(bearing)
    compass_bearing = (bearing + 360) % 360

    return compass_bearing



def get_data(eastnorth,radius,key,data_key,data_dict):
    if data_key == 'buildings':
        os_data_source = OSparam_feature(eastnorth[0], eastnorth[1], radius,'topographic_area',key, clip=False)
        if isinstance(os_data_source, str):
            linedistances="no data for lines"
            return os_data_source, linedistances
        else:
            os_data = os_data_source[os_data_source['Theme'] == 'Buildings'].set_crs(27700)
    else:
        os_data = OSparam_ngd(eastnorth[0], eastnorth[1], radius,data_dict[data_key],key, clip=False)
        if isinstance(os_data, str):
            linedistances="no data for lines"
            return os_data, linedistances
        elif os_data.crs is None:
            os_data.set_crs("EPSG:4326", inplace=True)

    point = Point(eastnorth[0], eastnorth[1])
    point_gdf = gpd.GeoDataFrame(geometry=[point], crs=27700)
    point_gdf = point_gdf.to_crs(os_data.crs)

    os_data = os_data.to_crs("EPSG:27700")  # Project to British National Grid
    point_gdf = point_gdf.to_crs("EPSG:27700")

    linedistances = os_data.shortest_line(point_gdf.geometry.iloc[0])
    os_data['distance_to_point'] = os_data.geometry.apply(lambda x: point_gdf.geometry.iloc[0].distance(x))
    os_data['bearing_to_point'] = os_data.geometry.apply(lambda x: calculate_bearing(point_gdf.geometry.iloc[0], x.centroid))

    if data_key == 'roads':
        os_data['road_orientation'] = os_data.geometry.apply(calculate_bearing_linestring)

    return os_data, linedistances