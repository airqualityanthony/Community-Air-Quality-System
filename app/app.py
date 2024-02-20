import streamlit as st
from streamlit_folium import st_folium
from os_functions import building_height_radius, get_data, calculate_bearing
import os
from convertbng.util import convert_bng
import folium
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import leafmap.foliumap as leafmap

key = os.environ.get('OS_API_KEY')
data_dict = {'average_speeds': 'trn-rami-averageandindicativespeed-1',
 'pavements': 'trn-ntwk-pavementlink-1',
 'pavement2': 'trn-ntwk-pavementlink-1',
 'roads': 'trn-ntwk-roadlink-2'}

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

# if st.button('Submit Model Coordinates'):
if st.checkbox("Submit Model Coordinates"):

    if st.session_state.lon:
        lon = st.session_state.lon
        lat = st.session_state.lat
    else:
        lon = longitudes[0]
        lat = latitudes[0]

    X,Y = convert_bng(lon,lat)

    try:
        try:
            buildings,buildings_lines = get_data([X,Y],50,key,'buildings',data_dict)
        except:
            pass
        roads,road_lines = get_data([X,Y],50,key,'roads',data_dict)
        pavement,pavement_lines = get_data([X,Y],50,key,'pavements',data_dict)

        fg.add_child(folium.GeoJson(buildings,popup=folium.GeoJsonPopup(fields=list(buildings.columns)[1:len(buildings.columns)]),style_function=lambda x: {'color':'red'}))
        fg.add_child(folium.GeoJson(roads,popup=folium.GeoJsonPopup(fields=list(roads.columns)[1:-1]),style_function=lambda x: {'color':'green'}))
        fg.add_child(folium.GeoJson(pavement,popup=folium.GeoJsonPopup(fields=list(pavement.columns)[1:-0]),style_function=lambda x: {'color':'blue'}))
        fg.add_child(folium.CircleMarker([lat, lon],popup=[lat,lon],radius=0.5,color='blue',fill=True,fill_color='black'))

        fg.add_child(folium.GeoJson(road_lines,style_function=lambda x: {'color':'orange','weight':0.7,'opacity':0.5}))
        fg.add_child(folium.GeoJson(pavement_lines,style_function=lambda x: {'color':'orange','weight':0.7,'opacity':0.5}))
        fg.add_child(folium.GeoJson(buildings_lines,style_function=lambda x: {'color':'orange','weight':0.7,'opacity':0.5}))


        result_map = leafmap.Map(center = [lat,lon], minimap_control = True, draw_control = False, zoom = 18)
        fg.add_to(result_map)
        ## load the map
        result_map.to_streamlit(
            center=[lat, lon],
            zoom=18,
            width=1200,
            height=500,
        )

        # location data output
        output_data = pd.DataFrame({'Latitude':[lat],'Longitude': [lon]})
        tab1, tab2, tab3 = st.tabs(["Buildings", "Roads", "Pavements"])

        with tab1:
            st.header("Buildings")
            st.dataframe(pd.DataFrame(buildings.drop(columns='geometry')))

        with tab2:
            st.header("Roads")
            st.dataframe(pd.DataFrame(roads.drop(columns='geometry')))
        with tab3:
            st.header("Pavements")
            st.dataframe(pd.DataFrame(pavement.drop(columns='geometry')))
        # output_data.to_csv('output_data.csv')
    except AttributeError:
        st.write("No data found in the area. Please select another location.")
else: 
    st.write("Please select a location before continuing.")
