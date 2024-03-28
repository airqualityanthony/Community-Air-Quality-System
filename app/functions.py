import geopandas as gpd
from shapely.geometry import LineString
import numpy as np
import math
from osdatahub import FeaturesAPI, Extent, NGD
from convertbng.util import convert_lonlat
from geopy.distance import geodesic
from shapely.geometry import Point
import geopandas as gpd
from meteostat import Daily, Point as metPoint, Hourly
import difflib
from datetime import datetime

ngd_collections = NGD.get_collections()
collections = {}

for i in ngd_collections['collections']:
    collections.update({i['title']:i['id']})

recipe = ['Average And Indicative Speed',
'Pavement Link',
'Pavement',
'Road Link',]


data_collections = [collections[difflib.get_close_matches(i, collections.keys())[0]] for i in recipe]
data_dict = {'average_speeds': data_collections[0], 'pavement1': data_collections[1], 'pavement2': data_collections[2], 'roads': data_collections[3]}



def calculate_bearing(pointA, pointB):
    if not (isinstance(pointA, tuple) and isinstance(pointB, tuple)):
        raise TypeError("Only tuples are supported")

    lat1 = math.radians(pointA[1])
    lat2 = math.radians(pointB[1])
    diffLong = math.radians(pointB[0] - pointA[0])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Normalize the initial bearing to a compass bearing (0 to 360 degrees)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def calculate_bearing_linestring(line):
    if isinstance(line, LineString):
        pointA = line.coords[0]
        pointB = line.coords[-1]
    else:
        raise TypeError("Only LineString objects are supported")

    lat1 = math.radians(pointA[1])
    lat2 = math.radians(pointB[1])
    diffLong = math.radians(pointB[0] - pointA[0])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Normalize the initial bearing to a compass bearing (0 to 360 degrees)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

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

def get_data(eastnorth,radius,key,data_key):
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
    # os_data['bearing_to_point'] = os_data.geometry.apply(lambda x: calculate_bearing(point_gdf.geometry.iloc[0], x.centroid))
    os_data['bearing_to_point'] = os_data.geometry.apply(lambda x: calculate_bearing((point_gdf.geometry.iloc[0].x, point_gdf.geometry.iloc[0].y), (x.centroid.x, x.centroid.y)))
    os_data_4326 = os_data.to_crs("EPSG:4326")
    point_gdf_ll = point_gdf.to_crs("EPSG:4326") 
    point_lon, point_lat = point_gdf_ll.geometry.iloc[0].x, point_gdf_ll.geometry.iloc[0].y
    # try:
    #     os_data['fwd_azimuth'], os_data['back_azimuth'], _ = zip(*os_data_4326.geometry.apply(lambda x: geodesic.inv(point_lon, point_lat, x.centroid.x, x.centroid.y)))
    # except:
    #     os_data['fwd_azimuth'], os_data['back_azimuth'] = None, None
    if data_key == 'roads':
        os_data['road_orientation'] = os_data.geometry.apply(calculate_bearing_linestring)        

    return os_data, linedistances

def met_data(lat,lon, start_date, end_date):
    met_point = metPoint(lat,lon)
    met_point.radius = 100000
    data = Daily(met_point, start_date, end_date).fetch()
    # data_h = Hourly(met_point, start_date, end_date).fetch()
    # data_h.reset_index(inplace=True)
    # data_h.resample('d', on='time').mean().dropna(how='all')
    return data
        
def building_side_wind(building_bearing, wind_direction, road_orientation):
    building_side = ((road_orientation - building_bearing) + ((road_orientation + 180)-building_bearing))
    wind_side = ((road_orientation - wind_direction) + ((road_orientation + 180)-wind_direction))
    if abs(building_side) > 180:
        building_side_side = "a"
    else:
        building_side_side = "b"
    
    if abs(wind_side) > 180:
        wind_side_side = "a"
    else:
        wind_side_side = "b"

    if building_side_side == wind_side_side:
        return "windward"
    else:
        return "leeward"
    
def building_side_road(road_bearing):
    if road_bearing < 45 or road_bearing > 315:
        return "north"
    elif road_bearing >= 45 and road_bearing < 135:
        return "east"
    elif road_bearing >= 135 and road_bearing < 225:
        return "south"
    else:
        return "west"

def wind_orientation(road_orientation, wind_direction):
    # Normalize the bearings to be between 0 and 360
    road_orientation = road_orientation % 360
    wind_direction = wind_direction % 360
    # Calculate the difference between the two bearings
    diff = abs(road_orientation - wind_direction)
    return diff

def canyon_factor(buildings_data,road_orientation,wind_direction,wind_speed):
        # Normalize the bearings to be between 0 and 360
    road_orientation = road_orientation % 360
    wind_direction = wind_direction % 360
    # Calculate the difference between the two bearings
    wind_diff = abs(road_orientation - wind_direction)
    ## count number of buildings on windward and leeward sides
    windward_count = len(buildings_data[buildings_data['building_side_wind']=="windward"])
    leeward_count = len(buildings_data[buildings_data['building_side_wind']=="leeward"])
    windward_height_avg = buildings_data[buildings_data['building_side_wind']=="windward"]['RelH2'].mean()
    leeward_height_avg = buildings_data[buildings_data['building_side_wind']=="leeward"]['RelH2'].mean()
    windward_factor = (windward_count * windward_height_avg) 
    leeward_factor = (leeward_count * leeward_height_avg)
    diff = windward_factor - leeward_factor

    if wind_diff < 15:
        return 0
    elif windward_factor > 10 and diff > 10:
        return 1*wind_speed
    elif windward_factor > 10 and diff < 10:
        return 2*wind_speed
    else:
        return 0