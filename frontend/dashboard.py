import streamlit as st
import pandas as pd
import numpy as np
import pytz
from datetime import datetime
from datetime import date
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import requests
from datetime import datetime
import altair as alt
from datetime import timedelta


# Set the URL of the backend
backend_url = "..."

####### Functions to get values from the backend #######

@st.cache_data(ttl=600)
def get_outdoor_values():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    return response

@st.cache_data(ttl=600)
def get_outdoor_temp():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    outdoor_temp = response['outdoor_temp']
    return outdoor_temp

@st.cache_data(ttl=600)
def get_outdoor_humidity():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    outdoor_humidity = response['outdoor_humidity']
    return outdoor_humidity

@st.cache_data(ttl=600)
def get_actual_outdoor_description():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    outdoor_weather = response['description']
    return outdoor_weather

@st.cache_data(ttl=600)
def get_actual_weather_icon():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    icon = response['icon']
    return icon

@st.cache_data(ttl=600)
def get_outdoor_feels_like():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    outdoor_feels_like = response['outdoor_feels_like']
    return outdoor_feels_like

@st.cache_data(ttl=600)
def get_wind():
    response = requests.get(f"{backend_url}/get_actual_outdoor_weather")
    response = response.json()
    outdoor_wind = response['wind']
    return outdoor_wind

@st.cache_data(ttl=600)
def get_weather_forecast():
    response = requests.get(f"{backend_url}/get_weather_forecast")
    if response.status_code != 200:
        raise Exception(f"GET /get_weather_forecast {response.status_code}")
    try:
        return response.json()
    except ValueError:
        raise Exception("Invalid response: not a valid JSON.")

@st.cache_data(ttl=600)
def get_weather_forecast_day():
    response = requests.get(f"{backend_url}/get_weather_forecast_day")
    if response.status_code != 200:
        raise Exception(f"GET /get_weather_forecast_day {response.status_code}")
    try:
        return response.json()
    except ValueError:
        raise Exception("Invalid response: not a valid JSON.")

@st.cache_data(ttl=600)
def get_historical_weather():
    response = requests.get(f"{backend_url}/get_bigquery_data")
    if response.status_code == 200:  # The request was successful
        if response.content:  # The response is not empty
            data = response.json()
            return data
        else:
            return 'The response is empty.'
    else:
        return f'The request failed with status code {response.status_code}.'




####### Other functions #######

def ChangeTheme():
  previous_theme = ms.themes["current_theme"]
  tdict = ms.themes["light"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]
  for vkey, vval in tdict.items(): 
    if vkey.startswith("theme"): st._config.set_option(vkey, vval)

  ms.themes["refreshed"] = False
  if previous_theme == "dark": ms.themes["current_theme"] = "light"
  elif previous_theme == "light": ms.themes["current_theme"] = "dark"
  
  

####### Dashboard #######

# Page setting
st.set_page_config(layout="wide", page_title="Weather Dashboard")

#background
ms = st.session_state
if "themes" not in ms: 
  ms.themes = {"current_theme": "light",
                    "refreshed": True,
                    
                    "light": {"theme.base": "dark",
                              "theme.backgroundColor": "black",
                              "theme.primaryColor": "#c98bdb",
                              "theme.secondaryBackgroundColor": "#5591f5",
                              "theme.textColor": "white",
                              "theme.textColor": "white",
                              "button_face": "🌜"},

                    "dark":  {"theme.base": "light",
                              "theme.backgroundColor": "white",
                              "theme.primaryColor": "#5591f5",
                              "theme.secondaryBackgroundColor": "#82E1D7",
                              "theme.textColor": "#0a1464",
                              "button_face": "🌞"},
                    }
  


btn_face = ms.themes["light"]["button_face"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]["button_face"]



#Title and buttons
manual, coltitle, colbutton = st.columns([4,5,1])


with coltitle:
    st.title("Weather Dashboard")
with colbutton:
    st.button(btn_face, on_click=ChangeTheme)
    
if ms.themes["refreshed"] == False:
  ms.themes["refreshed"] = True
  st.rerun()



#Autorefresh:
count = st_autorefresh(interval=60000, key="fizzbuzzcounter") # refresh every minute


#location
selected_location = "Lausanne"

#Time
nowTime = datetime.now()
current_time = nowTime.astimezone(pytz.timezone('Europe/Zurich')).strftime("%H:%M")
today = datetime.now(pytz.timezone('Europe/Zurich')).strftime("%A, %d %B")

col1, col2 = st.columns([1,3])

with col1:
    
    location = st.container(border=True, height=285)

    location.write(f"<h3 style='text-align: center;'>{selected_location}</h3>", unsafe_allow_html=True)
    location.write(f"<h1 style='text-align: center;'>{current_time}</h1>", unsafe_allow_html=True)
    location.write(f"<h4 style='text-align: center;'>{today}</h4>", unsafe_allow_html=True)


with col2:
    
    current_weather = st.container(border=True, height=285)

    outdoor, center, indoor = current_weather.columns([1,1,1])

    with outdoor:
        st.metric("Outdoor Temperature", f"{get_outdoor_temp()} °C")
        st.metric("Outdoor Humidity", f"{get_outdoor_humidity()} %")
        st.metric("Wind Speed", f"{get_wind()} m/s")
    
    with center:
       
        logo = get_actual_weather_icon()
        st.image(f"http://openweathermap.org/img/wn/{logo}@2x.png", width=150)
        st.write(f"<h3>{get_actual_outdoor_description()}</h3>", unsafe_allow_html=True) 
        
    with indoor:
        #get indoor data
        historical_data = get_historical_weather()
        df = pd.DataFrame(historical_data)
        df['datetime'] = pd.to_datetime(df['date'].str.slice(0, 16, 1) + ' ' + df['time'])
        df = df.sort_values('datetime')
        st.metric("Indoor Temperature", f"{df['indoor_temp'].iloc[-1]} °C")
        st.metric("Indoor Humidity", f"{df['indoor_humidity'].iloc[-1]} %")
        st.metric("CO2", f"{df['co2'].iloc[-1]} ppm")

daily, hourly = st.columns([1,2])

with daily:
    daily_forecast = st.container(border=True)
    daily_forecast.write(f"<h2 style='text-align: center;'> Daily Forecast </h2>", unsafe_allow_html=True)

    forecast_list_day = get_weather_forecast_day()
    cols = daily_forecast.columns(3)  

    for i, (day, forecast) in enumerate(list(forecast_list_day.items())[:3]):
        with cols[i]:  # Use each column for a forecast
            with st.container(border=True, height=300):
                # Convert date to datetime object and get the day of the week
                day_of_week = datetime.strptime(day, "%Y-%m-%d").strftime("%A")
                st.write(f"<h4 style='text-align: center;'>{day_of_week}</h4>", unsafe_allow_html=True)
                st.image(f"http://openweathermap.org/img/wn/{forecast['max_temp_icon']}@2x.png", width=50, use_column_width=True)
                st.write(f"<h4 style='text-align: center;'>{forecast['max_temp']} °C </h4>", unsafe_allow_html=True)
                
    
   
with hourly:
    hourly_forecast = st.container(border=True)
    hourly_forecast.write(f"<h2 style='text-align: center;'> Hourly Forecast </h2>", unsafe_allow_html=True)

    forecast_list = get_weather_forecast()[:7]
    num_forecasts = len(forecast_list)
    cols = hourly_forecast.columns(num_forecasts)  # Create a dynamic number of columns
    for i in range(num_forecasts):
        forecast = forecast_list[i]
        with cols[i]:  # Use each column for a forecast
            with st.container(border=True, height=300):
                #st.write(f"<h3>{forecast['date']}</h3>", unsafe_allow_html=True)
                st.write(f"<h3 style='text-align: center;'>{forecast['hour']}</h3>", unsafe_allow_html=True)
                st.image(f"http://openweathermap.org/img/wn/{forecast['icon']}@2x.png", width=50, use_column_width=True)
                st.write(f"<h3 style='text-align: center;'>{forecast['temperature']} °C </h3>", unsafe_allow_html=True)
                st.write(f"<h4 style='text-align: center;'>{forecast['wind']} m/s </h4>", unsafe_allow_html=True)


col3, col4 = st.columns([1,1])

parameters = st.container(border=True)
paramets_list = ["Indoor Temperature", "Indoor Humidity", "CO2", "Outdoor Temperature", "Outdoor Humidity", "Wind Speed"]

with parameters:
    with st.form(key='my_form', border=False):
        start, end, param1, param2 = st.columns([1,1,1,1])
        with start:
            start_date = st.date_input("Select a start date", value=date.today() - timedelta(days=7))
        with end:
            end_date = st.date_input("Select an end date", value=date.today())
        with param1:
            select_param = st.selectbox("Select the first Weather Parameter", paramets_list, index=0) #index is to select the default value
        with param2:
            select_param2 = st.selectbox("Select the second Weather Parameter", paramets_list, index=3) 
        
        submit_button = st.form_submit_button(label='Submit')

    
# Charts container      
with col3:
    temperature_history = st.container(border=True)

    historical_data = get_historical_weather()

    #if submit_button:
        # convert the dates to datetime
    start_date = pd.to_datetime(datetime.combine(start_date, datetime.min.time()))
    end_date = pd.to_datetime(datetime.combine(end_date, datetime.max.time()))
    
    # filter the dataframe based on the selected date range
    filtered_data = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
    
    
    ###Boxplot###

    filtered_data['date'] = filtered_data['datetime'].dt.date
    
    chart_outdoor = alt.Chart(filtered_data).mark_boxplot( color="#17becf").encode(
        x=alt.X('monthdate(date):O', title='Date'),
        y=alt.Y('outdoor_temp', title='Outdoor Temperature')
    ).properties(title='Outdoor Temperature').configure_axisX(labelAngle=0).configure_title(anchor='middle', fontSize=14, fontWeight='bold')
    
    
    temperature_history.altair_chart(chart_outdoor,use_container_width=True)



    ###Weather conditions###
with col4:
    weather_history = st.container(border=True)
    
    filtered_data_weather_history = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]

    # Count the number of occurrences of each weather condition
    weather_counts = filtered_data_weather_history["outdoor_weather"].value_counts().reset_index()
    
    # chart description
    chart_description = alt.Chart(weather_counts).mark_bar(size=50).encode(
        x=alt.X('index:O', title='Weather Conditions'),
        y=alt.Y("outdoor_weather:Q", title='Count')
    ).properties(title='Frequencies of Weather Conditions').configure_axisX(labelAngle=0).configure_title(anchor='middle', fontSize=14, fontWeight='bold')
    
    # Resize & Display the chart
    chart_description = chart_description.interactive()
    weather_history.altair_chart(chart_description, use_container_width=True)
    


### Interactive chart ### 
       

historical_weather = st.container(border=True)
historical_weather.write("Interactive Chart")
param_to_column = {
       "Indoor Temperature": "indoor_temp",
       "Indoor Humidity": "indoor_humidity",
       "CO2": "co2",
       "Wind Speed": "wind_speed",
       "Outdoor Temperature": "outdoor_temp",
       "Outdoor Humidity": "outdoor_humidity"
 
}

y_axis_label = {
    "Indoor Temperature": "Temperature (°C)",
    "Indoor Humidity": "Humidity (%)",
    "CO2": "CO2 (ppm)",
    "Wind Speed": "Wind Speed (m/s)",
    "Outdoor Temperature": "Temperature (°C)",
    "Outdoor Humidity": "Humidity (%)"
}

# filter the dataframe based on the selected date range
filtered_data_interactive = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
filtered_data_interactive_2 = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]

# assign the category
filtered_data_interactive = filtered_data_interactive.assign(category=select_param)
filtered_data_interactive_2 = filtered_data_interactive_2.assign(category=select_param2)

# set columns
filtered_data_interactive = filtered_data_interactive[[param_to_column[select_param], 'datetime', 'category']]
filtered_data_interactive_2 = filtered_data_interactive_2[[param_to_column[select_param2], 'datetime', 'category']]

# set index
filtered_data_interactive.set_index('datetime', inplace=True)
filtered_data_interactive_2.set_index('datetime', inplace=True)


# Créer le graphique à ligne
chart1 = alt.Chart(filtered_data_interactive.reset_index()).mark_line().encode(
    x=alt.X('datetime:T', title='Date'),
    y=alt.Y(param_to_column[select_param], title=y_axis_label[select_param]),
    color='category:N'  
).interactive()

chart2 = alt.Chart(filtered_data_interactive_2.reset_index()).mark_line().encode(
    x=alt.X('datetime:T', title='Date'),
    y=alt.Y(param_to_column[select_param2], title=y_axis_label[select_param2]),
    color='category:N'  
).interactive()


# select the right label type for the y axis
if select_param == select_param2:
    chart = (chart1 + chart2).resolve_scale(
        y = 'shared',
    ).properties(
        title=f'{select_param} over Time'
    ).configure_title(anchor='middle')
    
elif select_param.split()[1:] == select_param2.split()[1:]:
    chart = (chart1 + chart2).resolve_scale(
        y = 'shared',
    ).properties(
        title=f'{select_param} and {select_param2} over Time'
    ).configure_title(anchor='middle')
    
else:    
    chart = (chart1 + chart2).resolve_scale(
        y = 'independent'
    ).properties(
        title=f'{select_param} and {select_param2} over Time'
    ).configure_title(anchor='middle')
    


    
historical_weather.altair_chart(chart, use_container_width=True)
