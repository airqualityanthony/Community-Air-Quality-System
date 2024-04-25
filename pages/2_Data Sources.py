import streamlit as st
import pandas as pd
import os
import json
from google.cloud import firestore

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

st.sidebar.title("Bug Report")
st.sidebar.info("If you encounter any bugs, please report them below")
bug_report = st.sidebar.text_area("Enter Bug Report Here")
if st.sidebar.button("Submit Bug Report"):
    key_dict = json.loads(st.secrets["textkey"])
    # Convert dict to json and save it as a file
    with open('keyfile.json', 'w') as fp:
        json.dump(key_dict, fp)
    ## connec to DB
    db = firestore.Client.from_service_account_json('keyfile.json')
    data_dict = {'bug_report': bug_report, 'date': datetime.now()}
    ## write to firestore
    db.collection('bug_reports').add(data_dict)

    # remove the json file after done
    os.remove('keyfile.json')
    st.sidebar.write("Bug Report Submitted")

# Define the data for the table
data = {
    'Name': ['Meteostat', "{openair}", 'OS Data Hub'],
    'Description': ['Meteostat is one of the largest vendors of open weather and climate data. Access long-term time series of thousands of weather stations and integrate Meteostat data into your products, applications and workflows. Thanks to our open data policy, Meteostat is an ideal data source for research and educational projects.', 
                    'openair --- an R package for air quality data analysis', 
                    "Great Britain’s Geospatial Data platform."],
    'URL': ['https://meteostat.net/en/', 'https://davidcarslaw.github.io/openair/', 'https://osdatahub.os.uk/']
}

# Create a DataFrame from the data
df = pd.DataFrame(data)


# Display the data table
st.subheader('Data Sources Table')
## prettify the dataframe and make url column hyperlinks
df['URL'] = df['URL'].apply(lambda x: f'<a href="{x}">{x}</a>')
## write dataframe but don't show index, headers justified left
st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)






