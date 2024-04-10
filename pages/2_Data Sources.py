import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Sources", page_icon="🗃️", layout="wide")

st.title("Data Sources")

# Customize the sidebar
markdown = """
Citizen Air Quality System
CAQS is a citizen science project that aims to provide an open-source, 
and easy-to-use air quality modelling system for the public."""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.dailymail.co.uk/i/pix/2016/12/01/17/3AE49E8700000578-3986672-AirVisual_Earth_aims_to_clearly_show_the_effect_that_human_emiss-m-25_1480613072849.jpg"
st.sidebar.image(logo)


# Define the data for the table
data = {
    'Name': ['Data Source 1', 'Data Source 2', 'Data Source 3'],
    'Description': ['Description 1', 'Description 2', 'Description 3'],
    'URL': ['https://datasource1.com', 'https://datasource2.com', 'https://datasource3.com']
}

# Create a DataFrame from the data
df = pd.DataFrame(data)


# Display the data table
st.subheader('Data Sources Table')
st.dataframe(df)



