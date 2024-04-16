import streamlit as st
import os
from google.cloud import firestore

st.set_page_config(page_title="Modelling Output", page_icon="📈", layout="wide")

st.title("Modelling Output")

# Customize the sidebar
markdown = """
Citizen Air Quality System
CAQS is a citizen science project that aims to provide an open-source, 
and easy-to-use air quality modelling system for the public."""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://i.dailymail.co.uk/i/pix/2016/12/01/17/3AE49E8700000578-3986672-AirVisual_Earth_aims_to_clearly_show_the_effect_that_human_emiss-m-25_1480613072849.jpg"
st.sidebar.image(logo)



if st.session_state['output']==True:
    ## load data
    import pandas as pd
    data = pd.read_csv('output_data.csv')

    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LinearRegression 
    from sklearn.metrics import mean_squared_error, r2_score
    import numpy as np

    data['date']  = pd.to_datetime(data['time'])
    data['month'] = data['date'].dt.month
    data['year'] = data['date'].dt.year
    data['day'] = data['date'].dt.day
    data['jdate'] = pd.DatetimeIndex(data['date']).to_julian_date()
    data.head()
    
    selected_columns = data.select_dtypes(include=['float64','int64','int32'])
    selected_columns = selected_columns.drop(columns=['snow','tsun'])
    selected_columns.head()

    ## fill NaN with mean

    selected_columns = selected_columns.fillna(selected_columns.mean())

    X_postprocess = selected_columns

    ## train model
    ## xgboost 
    from xgboost import XGBRegressor

    ## read in pkl file for model
    import pickle
    postprocess_model = pickle.load(open('xgboost_model.pkl','rb'))

    ## predict

    y_pred_post = postprocess_model.predict(X_postprocess)

    ## add to dataframe
    data['no2_pred'] = y_pred_post

    st.write(data)
    from prophet import Prophet


    ## create dataframe for prophet
    prophet_data = data[['date','no2_pred']]
    prophet_data['floor'] = 1
    prophet_data['cap'] = 200
    prophet_data.columns = ['ds','y','floor','cap']


    ## train prophet model
    m = Prophet(growth='logistic')
    m.fit(prophet_data)

    ## calculate how many days in the max year available in the prophet data
    max_year = prophet_data['ds'].dt.year.max()
    max_date = prophet_data[prophet_data['ds'].dt.year==max_year]['ds'].max()
    ## calculate how many days left in the max_date year
    max_date = pd.to_datetime(max_date)
    end_of_year = pd.to_datetime(f'{max_date.year}-12-31')
    days_left = end_of_year - max_date
    
    ## set periods to complete the year and the next 5 years
    periods = days_left.days + 365*5

    ## make future dataframe
    future = m.make_future_dataframe(periods=periods)
    future['floor'] = 1
    future['cap'] = 200
    forecast = m.predict(future)
    ## subset to only future dates

    forecast = forecast[forecast['ds']>data['date'].max()]

    ## plot original data and forecast data with plotly
    import plotly.graph_objects as go
    fig = go.Figure()
    ## add title to plot

    fig.update_layout(title='NO2 Modelled with XGBoost and Future Forecast with Prophet')
    ## Add the original data
    fig.add_trace(go.Scatter(x=data['date'], y=data['no2_pred'], mode='lines', name='no2 modelled with xgboost'))
    # Add the forecast line
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='no2 forecasted with prophet'))
    # Add upper bound line
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', name='no2 upper bound forecasted with prophet', line=dict(width=0)))
    # Add lower bound line
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', name='no2 lower bound forecasted with prophet', line=dict(width=0), fill='tonexty'))

    st.plotly_chart(fig, use_container_width=True)

    st.write(forecast)

    ## write run to DB 
    # Import the library


    # Authenticate to Firestore with the JSON account key.
    # db = firestore.Client.from_service_account_json("firestore-key.json")
    import json
    key_dict = json.loads(st.secrets["textkey"])
    ## convert to json

        # Convert dict to json and save it as a file
    with open('keyfile.json', 'w') as fp:
        json.dump(key_dict, fp)

    # Now you can use this json file to authenticate
    db = firestore.Client.from_service_account_json('keyfile.json')

    # Remember to remove the json file after you're done
    os.remove('keyfile.json')

    # Define your groupby columns and aggregation functions
    groupby_columns = ['year', 'latitude', 'longitude']
    
    ## subset data
    data_sub = data[['year','latitude','longitude','tavg','tmin','tmax','wdir','wspd','elevation','u','v','canyon_factor','windward_height_avg','leeward_height_avg','road_distance','indicatedspeed_kph','no2_pred']]
    # Use groupby and agg
    aggregated_output = data_sub.groupby(groupby_columns).mean().reset_index()
    aggregated_output['type'] = 'modelled'
    # st.write(aggregated_output)

    ## aggregate the forecast data
    ### add year column to forecast
    forecast['year'] = forecast['ds'].dt.year
    forecast['no2_pred'] = forecast['yhat']
    groupby_columns = ['year']
    aggregation_functions = {'no2_pred': 'mean'}

    # Use groupby and agg
    aggregated_forecast = forecast.groupby(groupby_columns).agg(aggregation_functions).reset_index()
    ## add longitude and latitude
    aggregated_forecast['latitude'] = data['latitude'].mean()
    aggregated_forecast['longitude'] = data['longitude'].mean()
    aggregated_forecast['type'] = 'forecast'

    # ## add to aggregated_output not using append
    merged_agg = pd.concat([aggregated_output,aggregated_forecast],axis=0)
    
    ## add runTime and runUniqueId
    merged_agg['runTime'] = pd.to_datetime('now')
    import uuid

    # Generate a unique ID
    runUniqueId = str(uuid.uuid4())

    # Add the unique ID to your DataFrame
    merged_agg['runUniqueId'] = runUniqueId

    ## write to firestore
    ## convert to dictionary
    data_dict = merged_agg.to_dict(orient='records')


    ## write to firestore
    for record in data_dict:
        db.collection('app_runs').add(record)

    st.write("Data has been written to Firestore")

else:
    st.write("No output data has been generated")