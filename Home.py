import streamlit as st
from streamlit_folium import st_folium, folium_static
from functions import get_data, met_data, calculate_bearing, building_side_wind, building_side_road, canyon_factor
import os
from convertbng.util import convert_bng
import folium
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import leafmap.foliumap as leafmap
from datetime import datetime
import numpy as np


if st.secrets["OS_API_KEY"] is None:
    key = os.environ.get('OS_API_KEY')
else:
    key = st.secrets["OS_API_KEY"]


data_dict = {'average_speeds': 'trn-rami-averageandindicativespeed-1',
 'pavements': 'trn-ntwk-pavementlink-1',
 'pavement2': 'trn-ntwk-pavementlink-1',
 'roads': 'trn-ntwk-roadlink-2'}


## create output in session state and set to False
if 'output' not in st.session_state:
    st.session_state['output'] = False


st.set_page_config(page_title="Home", page_icon="☁️", layout="wide")


# Customize the sidebar
markdown = """
Citizen Air Quality System
CAQS is a citizen science project that aims to provide an open-source, 
and easy-to-use air quality modelling system for the public."""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.dailymail.co.uk/i/pix/2016/12/01/17/3AE49E8700000578-3986672-AirVisual_Earth_aims_to_clearly_show_the_effect_that_human_emiss-m-25_1480613072849.jpg"
st.sidebar.image(logo)

# Customize page title
st.title("Citizen Air Quality System - Web App")

st.markdown(
    """
    This web app allows users to place markers on the below interactive map, and leverage open source APIs to automate and conduct air quality concentration modelling
    """
)


st.header("Instructions")

markdown = """
1. Place a marker using the toolset on the left of the map 
2. Select which year you would like to predict the concentration at the point for. 
3. Hit Submit and wait for the model to run.
4. Once complete head to the Modelling Output page to see the results.
"""

st.markdown(markdown)

st.title("Map")


m = folium.Map(location=[51.23, -1.00], zoom_start=5)
fg = folium.FeatureGroup(name="data")
Draw().add_to(m)

map_placeholder = st.empty()

with map_placeholder:
    mapdata = st_folium(
    m,
    feature_group_to_add=fg,
    center=[51.23, -1.00],
    width=1200,
    height=500,)
## Write Drawing Data to Streamlit
longitudes = []
latitudes = []

st.write("or enter coordinates below")

latcol, loncol = st.columns(2)

with latcol:    
    st.number_input("Latitude", key="lat",step=1e-5,help="Enter latitude in decimal degrees",format="%.5f")

with loncol:
    st.number_input("Longitude", key="lon",step=1e-5,help="Enter longitude in decimal degrees",format="%.5f")


if mapdata['all_drawings']:
    for i in range(0,len(mapdata['all_drawings'])):
        longitudes.append(mapdata['all_drawings'][i]['geometry']['coordinates'][0])
        latitudes.append(mapdata['all_drawings'][i]['geometry']['coordinates'][1])

else: 
    st.write("Please select markers before continuing.")


start_date = st.date_input("Start Date", key="start_date", value=datetime(2018, 1, 1))
end_date = st.date_input("End Date", key="end_date", value=datetime.today())


start_date = datetime.combine(start_date, datetime.min.time())
end_date = datetime.combine(end_date, datetime.min.time())


radius = st.number_input("Radius (m)", key="radius", value=75, step=25)

#### ============= Data Retrieval ================== ####
if st.button("Submit Model Coordinates"):

    if st.session_state.lon:
        lon = st.session_state.lon
        lat = st.session_state.lat
    else:
        lon = longitudes[0]
        lat = latitudes[0]

    try:
        buildings_df = gpd.GeoDataFrame()
        roads_df = gpd.GeoDataFrame()
        pavement_df = gpd.GeoDataFrame()
        averagespeed_df = gpd.GeoDataFrame()
        building_lines = gpd.GeoSeries()
        roads_lines = gpd.GeoSeries()
        pavement_lines = gpd.GeoSeries()
        speed_lines = gpd.GeoSeries()
        met_df = pd.DataFrame()

        eastnorth = convert_bng(lon,lat)
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

        metdata = met_data(lat,lon, start_date, end_date)
        metdata['latitude'] = lat
        metdata['longitude'] = lon
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


        # Initialize the progress bar
        
        st.write("Gathering Data Please Wait...")
        progress_bar = st.empty()


        for index, met_day in enumerate(met_df.index):
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

            # Update the progress bar
            progress_bar.progress((index + 1) / len(met_df.index))
            output = met_df.copy()
        progress_bar.empty()
        st.write(output)
        st.write("Data Collection Complete")
        output.to_csv('output_data.csv',index=True)    
        st.session_state['output'] = True
    except AttributeError:
        st.write("No data found in the area. Please select another location.")

    ## select which day to filter the met data for building windward and leeward visualisation
    met_day = st.number_input("Select Day", key="met_day", value=20, min_value=0, max_value=len(met_df)-1, step=1)

    ## plot the map based on the filter - if the filter changes the map will update
    st.write("Map of the area with buildings and roads")

    #
    ## plot 3D Map
    import pydeck as pdk
    
    min_RelH2 = buildings_df['RelH2'].min()
    range_RelH2 = buildings_df['RelH2'].max() - min_RelH2

    # met_gpd = gpd.GeoDataFrame(met_df, geometry=gpd.points_from_xy(met_df.longitude, met_df.latitude))
    met_gpd = output.copy()

    buildings_df = buildings_df.to_crs(epsg=4326)
    roads_df = roads_df.to_crs(epsg=4326)


    buildings_df['building_side_wind'] = buildings_df['bearing_to_road'].apply(lambda x: building_side_wind(x, met_gpd['wdir'].iloc[met_day],roads_df['road_orientation'].iloc[0]))
    buildings_df['building_side_road'] = buildings_df['bearing_to_road'].apply(lambda x: building_side_road(x))


    roads_df['start_lon'], roads_df['start_lat'] = roads_df.geometry.apply(lambda x: x.coords[0][0]), roads_df.geometry.apply(lambda x: x.coords[0][1])
    roads_df['end_lon'], roads_df['end_lat'] = roads_df.geometry.apply(lambda x: x.coords[-1][0]), roads_df.geometry.apply(lambda x: x.coords[-1][1])

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
    # st.write(buildings_df)

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

    ## create a marker layer for the lat and lon site
    site_marker = pdk.Layer(
        "ScatterplotLayer",
        met_gpd.iloc[met_day:met_day+1],
        get_position=["longitude", "latitude"],
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

    # st.write(met_gpd.head())
    # Create ArrowLayer to indicate wind direction and speed for given met_day
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
        longitude=lon, latitude=lat, zoom=17, min_zoom=5, max_zoom=20, pitch=0, bearing=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[building_layer,road_layer,arrow_layer,site_marker],
        initial_view_state=view_state,
        map_style="light",
    ))


else: 
    st.write("Please select a location before continuing.")
