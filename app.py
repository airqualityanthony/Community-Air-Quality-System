import streamlit as st
import geemap.foliumap as geemap
import ee
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# Customize the sidebar
markdown = """
Citizen Air Quality System
CAQS is a citizen science project that aims to provide an open-source, 
and easy-to-use air quality modelling system for the public."""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.imgur.com/UbOXYAU.png"
st.sidebar.image(logo)

# Customize page title
st.title("Earth Engine Web App")

st.markdown(
    """
    This multipage app template demonstrates various interactive web apps created using [streamlit](https://streamlit.io) and [geemap](https://geemap.org). It is an open-source project and you are very welcome to contribute to the [GitHub repository](https://github.com/giswqs/geemap-apps).
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

m = geemap.Map(center=[51, -1], 
                zoom=4,
                draw_export=True)

# m.to_streamlit(height=700)

mapdata = st_folium(m, width=1500, height=700)

## Write Drawing Data to Streamlit
st.write(mapdata['all_drawings'])

if st.button("Submit Model Coordinates"):
    # roi = ee.FeatureCollection(m.draw_features)
    # st.write(roi.getInfo())
    pass
