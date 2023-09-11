import ee
import streamlit as st
import geemap.foliumap as geemap
from streamlit_folium import st_folium
import datetime


st.header("CAMS NO2 monitoring")
# Create an interactive map
Map = geemap.Map(center=[40, -100], zoom=4)

# Get an NLCD image by year.

dataset = ee.ImageCollection('ECMWF/CAMS/NRT')

# Use an ee.DateRange object.
start_date = st.date_input("Start Date", datetime.date(2022, 7, 1))
end_date = st.date_input("End Date", datetime.date(2022, 8, 1))

date_range = ee.DateRange(str(start_date), str(end_date))
data = dataset.filterDate(date_range)


##Select first and last forecast hours.
hour00 = data.filter('model_forecast_hour == 0').first()
hour21 = data.filter('model_forecast_hour == 21').first()



## Visualization parameters for specified aerosol band.
visParams = {
  'bands': ['total_aerosol_optical_depth_at_550nm_surface'],
  'min': 0.0,
  'max': 3.6,
  'palette': ['5e4fa2', '3288bd', '66c2a5', 'abe0a4', 'e6f598', 'ffffbf',
    'fee08b', 'fdae61', 'f46d43', 'd53e4f', '9e0142']
}

# Display forecasts on the map.
Map.setCenter(70, 45, 3)
Map.addLayer(hour00, visParams, 'total_column_nitrogen_dioxide_surface - H00', 'true', 0.6)
Map.addLayer(hour21, visParams, 'total_column_nitrogen_dioxide_surface - H21', 'true', 0.6)

st_folium(Map, width=1500, height=700)
