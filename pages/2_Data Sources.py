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
    'Name': ['Data Source 1', 'Data Source 2', 'Data Source 3'],
    'Description': ['Description 1', 'Description 2', 'Description 3'],
    'URL': ['https://datasource1.com', 'https://datasource2.com', 'https://datasource3.com']
}

# Create a DataFrame from the data
df = pd.DataFrame(data)


# Display the data table
st.subheader('Data Sources Table')
st.dataframe(df)



