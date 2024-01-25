import streamlit as st
from streamlit_folium import st_folium
from app.os_functions import building_height_radius
import os
from convertbng.util import convert_bng
import folium
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

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


m = folium.Map(location=[51.23, -1.00], zoom_start=5)
fg = folium.FeatureGroup(name="data")
Draw().add_to(m)


mapdata = st_folium(
    m,
    feature_group_to_add=fg,
    center=[51.23, -1.00],
    width=1200,
    height=500,
)
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

# if st.button('Submit Model Coordinates'):
if st.checkbox("Submit Model Coordinates"):

    lon = longitudes[0]
    lat = latitudes[0]

    X,Y = convert_bng(lon,lat)

    try:
        #```Buildings```
        TA = building_height_radius(X,Y, 100, 'topographic_area', key, True)
        ta_map = TA.explore('RelH2',width=1500, height=700) ## colour by height
        fg.add_child(folium.Marker([lat, lon],popup=[lat,lon]))
        Buildings = TA[TA['Theme']=="Buildings"]
        BuildingGeoSeries = TA['geometry'][TA['Theme'] == 'Buildings']
        BuildingGeoSeries = BuildingGeoSeries.to_crs(27700)
        BuildingDistances = BuildingGeoSeries.distance(Point(X,Y))
        LineDistances = BuildingGeoSeries.shortest_line(Point(X,Y))
        geo_j = folium.GeoJson(data=LineDistances, name="LineDistances", style_function=lambda x: {'color': 'red', 'weight': 0.5, 'opacity':0.5})
        ## add LineDistances to map
        fg.add_child(geo_j)
        ## add Buildings to map
        fg.add_child(folium.GeoJson(data=BuildingGeoSeries, name="Buildings", style_function=lambda x: {"color":"black",'weight': 1, 'opacity':0.5}))
        
        ## load the map
        mapdata = st_folium(
            m,
            feature_group_to_add=fg,
            center=[lat, lon],
            zoom=18,
            width=1200,
            height=500,
        )

        ## location data output
        output_data = pd.DataFrame({'Latitude':[lat],'Longitude': [lon]})
        st.dataframe(output_data)
        # output_data.to_csv('output_data.csv')
    except AttributeError:
        st.write("No buildings found in the area. Please select another location.")
else: 
    st.write("Please select a location before continuing.")
