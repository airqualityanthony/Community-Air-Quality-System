import streamlit as st
import geemap.foliumap as geemap
import ee
from streamlit_folium import st_folium
import json
from os_functions import building_height_radius
from osdatahub import FeaturesAPI, Extent, NGD
import os
from convertbng.util import convert_bng, convert_lonlat
import folium
import geopandas as gpd
from shapely.geometry import Point

key = os.environ.get('OS_API_KEY')

st.set_page_config(layout="wide")

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

m = geemap.Map(center=[54, 1], 
                zoom=6,
                draw_export=True)

# m.to_streamlit(height=700)

mapdata = st_folium(m, width=1500, height=700)

## Write Drawing Data to Streamlit
longitudes = []
latitudes = []

# st.write(len(mapdata['all_drawings']))

if mapdata['all_drawings']:
    for i in range(0,len(mapdata['all_drawings'])):
        longitudes.append(mapdata['all_drawings'][i]['geometry']['coordinates'][0])
        latitudes.append(mapdata['all_drawings'][i]['geometry']['coordinates'][1])

else: 
    st.write("Please select markers before continuing.")



year = st.selectbox('Select Year', range(2023,2040))

if st.checkbox("Submit Model Coordinates"):
    json_dump = {
                "latitudes": latitudes,
                "longitudes": longitudes,
                "year": year
                }
    
    lon = longitudes[0]
    lat = latitudes[0]

    X,Y = convert_bng(lon,lat)

    try:
        TA = building_height_radius(X,Y, 100, 'topographic_area', key, True)
        map = TA.explore('RelH2',width=1500, height=700) ## colour by height
        folium.Marker([lat, lon],popup=[lat,lon]).add_to(map)
        folium.plugins.MeasureControl().add_to(map)

        BuildingGeoSeries = TA['geometry'][TA['Theme'] == 'Buildings']
        BuildingGeoSeries = BuildingGeoSeries.to_crs(27700)
        BuildingDistances = BuildingGeoSeries.distance(Point(X,Y))
        LineDistances = BuildingGeoSeries.shortest_line(Point(X,Y))
        geo_j = folium.GeoJson(data=LineDistances, name="LineDistances", style_function=lambda x: {'color': 'red', 'weight': 1, 'opacity':0.5})
        geo_j.add_to(map)

        st_folium(map,width=1500, height=700)
        # st.write(TA)


    except AttributeError:
        st.write("No buildings found in the area. Please select another location.")

    
    with open('model_coordinates.json', 'w') as f:
        json.dump(json_dump, f)

