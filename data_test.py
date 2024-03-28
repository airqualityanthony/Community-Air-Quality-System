from app.functions import get_data, calculate_bearing, met_data, building_side_wind, building_side_road, wind_orientation, canyon_factor
import os
from convertbng.util import convert_bng
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
from datetime import datetime
from osdatahub import NGD
import difflib


key = os.environ.get('OS_API_KEY')


latitude = 51.00687392304635
longitude =  -0.9378286510368773
start_date = datetime(2018, 1, 1)
end_date = datetime.today()

radius = 75



buildings_df = gpd.GeoDataFrame()
roads_df = gpd.GeoDataFrame()
pavement_df = gpd.GeoDataFrame()
averagespeed_df = gpd.GeoDataFrame()
building_lines = gpd.GeoSeries()
roads_lines = gpd.GeoSeries()
pavement_lines = gpd.GeoSeries()
speed_lines = gpd.GeoSeries()
met_df = pd.DataFrame()


eastnorth = convert_bng(longitude,latitude)
buildings, buildingslines = get_data(eastnorth,radius,key,'buildings')
averagespeed, averagespeedlines = get_data(eastnorth,radius,key,'average_speeds')
pavement, pavementlines = get_data(eastnorth,radius,key,'pavement1')
road, roadlines = get_data(eastnorth,radius,key,'roads')

if isinstance(buildings, str):
    print("No buildings found")

if isinstance(averagespeed, str):
    print("No speed data found")
else:
    averagespeed_data = averagespeed.set_crs(27700)


if isinstance(pavement, str):
    print("No pavement data found")
else:
    pavement_data = pavement.set_crs(27700)

if isinstance(road, str):
    print("No road data found")
else:
    road_data = road.set_crs(27700)
    ## filter road data to closest to point 
    road_data = road_data[road_data['distance_to_point'] == road_data['distance_to_point'].min()]

try:
    average_elev = sum(list(buildings['AbsH2'] - buildings['RelH2']))/len(list(buildings['AbsH2'] - buildings['RelH2']))
except: 
    average_elev = None

metdata = met_data(latitude,longitude, start_date, end_date)
metdata['latitude'] = latitude
metdata['longitude'] = longitude
metdata['elevation'] = average_elev
metdata['u'] = metdata['wspd'] * np.cos(metdata['wdir'])
metdata['v'] = metdata['wspd'] * np.sin(metdata['wdir'])
## building calculated bearing to closest road
buildings['bearing_to_road'] =  buildings.geometry.apply(lambda x: calculate_bearing((road_data.geometry.iloc[0].centroid.x, road_data.geometry.iloc[0].centroid.y), (x.centroid.x, x.centroid.y)))


met_df = pd.concat([met_df,metdata])
buildings_df = pd.concat([buildings_df,buildings])
buildings_lines = pd.concat([building_lines,buildingslines])
averagespeed_df = pd.concat([averagespeed_df,averagespeed_data])
speed_lines = pd.concat([speed_lines,averagespeedlines])
pavement_df = pd.concat([pavement_df,pavement_data])
pavement_lines = pd.concat([pavement_lines,pavementlines])
roads_df = pd.concat([roads_df,road_data])
roads_lines = pd.concat([roads_lines,roadlines])


output = pd.DataFrame()

met_df['canyon_factor'] = "N/A"
met_df['windward_height_avg'] = "N/A"
met_df['leeward_height_avg'] = "N/A"
met_df['road_distance'] = "N/A"
met_df['indicatedspeed_kph'] = "N/A"

from tqdm import tqdm

for met_day in tqdm(met_df.index):
    buildings['building_side_wind'] = buildings['bearing_to_road'].apply(lambda x: building_side_wind(x, met_df.loc[met_day, 'wdir'],road['road_orientation'].iloc[0]))
    buildings['building_side_road'] = buildings['bearing_to_road'].apply(lambda x: building_side_road(x))
    cf = canyon_factor(buildings,road['road_orientation'].iloc[0],met_df.loc[met_day, 'wdir'],met_df.loc[met_day, 'wspd'])
    met_df.loc[met_day, 'canyon_factor'] = cf

    if len(buildings[buildings['building_side_wind']=="windward"]) == 0:
        met_df.loc[met_day, 'windward_height_avg'] = 0
    else:
        met_df.loc[met_day, 'windward_height_avg'] = buildings[buildings['building_side_wind']=="windward"]['RelH2'].mean()
    if len(buildings[buildings['building_side_wind']=="leeward"]) == 0:
        met_df.loc[met_day, 'leeward_height_avg'] = 0
    else:
        met_df.loc[met_day, 'leeward_height_avg'] = buildings[buildings['building_side_wind']=="leeward"]['RelH2'].mean()

    met_df.loc[met_day, 'road_distance'] = road['distance_to_point'].iloc[0]
    met_df.loc[met_day, 'indicatedspeed_kph'] = averagespeed_df['indicativespeedlimit_kph'].iloc[0]

output = met_df.copy()


## plot 3D Map
import pydeck as pdk
met_day = 20
min_RelH2 = buildings_df['RelH2'].min()
range_RelH2 = buildings_df['RelH2'].max() - min_RelH2

met_gpd = gpd.GeoDataFrame(met_df, geometry=gpd.points_from_xy(met_df.longitude, met_df.latitude))

buildings_df['building_side_wind'] = buildings_df['bearing_to_road'].apply(lambda x: building_side_wind(x, met_gpd['wdir'].iloc[met_day],roads_df['road_orientation'].iloc[0]))
buildings_df['building_side_road'] = buildings_df['bearing_to_road'].apply(lambda x: building_side_road(x))

def get_color_from_RelH2(RelH2):
    normalized_RelH2 = (RelH2 - min_RelH2) / range_RelH2
    if normalized_RelH2 < 0.5:
        # Transition from green to yellow for the first half of the range
        return [normalized_RelH2 * 2 * 255, 255, 0]
    else:
        # Transition from yellow to red for the second half of the range
        return [255, 255 - ((normalized_RelH2 - 0.5) * 2 * 255), 0]

# Apply the function to the RelH2 column to get the colors
# AURN_buildings_subset['color'] = AURN_buildings_subset['RelH2'].apply(get_color_from_RelH2)

# get color from building_side_wind variable
def get_color_from_building_side_wind(building_side_wind):
    if building_side_wind == "windward":
        return [255, 0, 0]  # Red for windward
    elif building_side_wind == "leeward":
        return [0, 255, 0]  # Green for leeward

# Apply the function to the building_side_wind column to get the colors
buildings_df['color'] = buildings_df['building_side_wind'].apply(get_color_from_building_side_wind)

building_layer = pdk.Layer(
    "GeoJsonLayer",
    buildings_df,
    opacity=1,
    stroked=True,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation="RelH2",
    get_fill_color='color',
    get_line_color=[255, 60, 255],
    pickable=True,
)

road_layer = pdk.Layer(
    "LineLayer",
    roads_df,
    get_source_position=['start_lon', 'start_lat'],
    get_target_position=['end_lon', 'end_lat'],
    opacity=1,
    stroked=True,
    filled=True,
    extruded=True,
    wireframe=True,
    get_width='roadwidth_average',
    get_color=[0, 0, 255],
    pickable=True
)

## create a marker layer for the AURN site
site_marker = pdk.Layer(
    "ScatterplotLayer",
    get_position=[longitude, latitude],
    get_fill_color=[255, 0, 0],
    get_line_color=[0, 0, 0],
    get_radius=2,
    extruded=True,
    get_elevation=20,
    pickable=True,
    auto_highlight=True,
    highlight_color=[255, 255, 0, 255],
)


# Extract wind direction and speed
wind_direction = met_gpd['wdir']  # replace with your column name
wind_speed = met_gpd['wspd']  # replace with your column name

# Convert wind speed to km/h
wind_speed_kmh = wind_speed / 3.6

## Convert wind direction from meteorological terms to mathematical terms
wind_direction_math = 360 + wind_direction

# Convert wind direction to radians
wind_direction_rad = np.deg2rad(wind_direction_math)

# Calculate end coordinates of the arrow based on wind direction and speed
# Divide wind_speed_kmh by a large number to bring the end coordinates closer to the original point
met_gpd['end_lon'] = met_gpd['longitude'] + np.sin(wind_direction_rad) * wind_speed_kmh / 10000
met_gpd['end_lat'] = met_gpd['latitude'] + np.cos(wind_direction_rad) * wind_speed_kmh / 10000

# Define a function to map wind speed to color
def get_color_from_speed(speed):
    if speed < 10:
        return [255, 0, 0]  # Red for speed < 10
    elif speed < 20:
        return [255, 255, 0]  # Yellow for 10 <= speed < 20
    else:
        return [0, 255, 0]  # Green for speed >= 20

# Apply the function to the wind_speed_kmh column to get the colors
met_gpd['color'] = met_gpd['wspd'].apply(get_color_from_speed)


# Create ArrowLayer
arrow_layer = pdk.Layer(
    "LineLayer",
    met_gpd.iloc[met_day:met_day+1],
    get_source_position=['longitude', 'latitude',50],
    get_target_position=['end_lon', 'end_lat',50],
    get_width=3,
    pickable=True,
    auto_highlight=True,
    get_color='color',
    opacity=0.5,
)

    
    # Set the viewport location
view_state = pdk.ViewState(
    longitude=longitude, latitude=latitude, zoom=17, min_zoom=5, max_zoom=20, pitch=0, bearing=0
)

# Combined all of it and render a viewport
r = pdk.Deck(
    layers=[building_layer,road_layer,arrow_layer,site_marker],
    initial_view_state=view_state,
    map_style="light",
)

r.to_html("3dmap.html")