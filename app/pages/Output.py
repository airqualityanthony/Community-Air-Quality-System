import streamlit as st
import geemap.foliumap as geemap

st.title("Modelling Output")


if st.session_state['output']==True:
    ## load data
    import pandas as pd
    data = pd.read_csv('output_data.csv')

    st.write(data)

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

    ## plot
    import plotly.express as px

    fig = px.line(data, x='date', y='no2_pred', title='Modelled NO2 Concentration')

    st.plotly_chart(fig)
else:
    st.write("No output data has been generated")