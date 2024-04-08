import streamlit as st

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
    prophet_data.columns = ['ds','y']

    ## train prophet model
    m = Prophet()
    m.fit(prophet_data)

    ## make future dataframe
    future = m.make_future_dataframe(periods=730)
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


else:
    st.write("No output data has been generated")