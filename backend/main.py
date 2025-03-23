from flask import Flask, request, jsonify, Response, send_file
import os
from google.cloud import bigquery
from google.cloud import texttospeech
import requests
from openai import OpenAI
import pandas as pd
import yaml
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import pytz
import collections

#Load keys and passwords
with open("keys.yaml", "r") as file:
    keys = yaml.safe_load(file)

#Image Font Path
font_path = "Mont-Regular.ttf"

#OpenAi credentials
OpenAI_client = OpenAI(api_key=keys["openAI_api_key"])

#Openweathermap credentials
OW_API_KEY = keys["openweathermap_api"]

#Location
location = "Lausanne"

#GCP Authentication
project_id = keys["project_id"]
dataset = keys["dataset"]

client = bigquery.Client(project=project_id)
tts_client = texttospeech.TextToSpeechClient()

#Hash password
HASH_PASSWORD = keys["HASH_PASSWORD"]

# Instantiate the Flask app
app = Flask(__name__)

# Define a route for the home page
@app.route('/')
def index():
    return "Welcome to the Weather App backend!"

# get the column names of the db
q = f"""
SELECT * FROM `{dataset}` LIMIT 10 
"""
query_job = client.query(q)
df = query_job.to_dataframe()

#Send data to Bigquery
@app.route('/send-to-bigquery', methods=['GET', 'POST'])
def send_to_bigquery():
    if request.method == 'POST':
        # Check if the password is correct
        if request.get_json(force=True)["passwd"] != HASH_PASSWORD: 
            raise Exception("Incorrect Password!")
        
        # Get the data values from M5Stack
        data = request.get_json(force=True)["values"]
        
        #Openweather map for outdoor weather
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
        response = requests.get(url).json()
        response = response["list"][0]
        
        data["outdoor_temp"] = round(response["main"]["temp"], 1)
        data["outdoor_humidity"] = response["main"]["humidity"]
        data["outdoor_weather"] = response["weather"][0]["description"]
        data["wind_speed"] = response["wind"]["speed"]
        
        # Add the current date and time
        timezone = pytz.timezone('Europe/Zurich')
        current_time = datetime.now(timezone)
        data["date"] = current_time.strftime('%Y-%m-%d')
        data["time"] = current_time.strftime('%H:%M:%S')
        
        # Add the data to the BigQuery table
        
        q = f"""INSERT INTO `{dataset}` 
        """
        names = """"""
        values = """"""
        for k, v in data.items():
            names += f"""{k},"""
            if df.dtypes[k] == float or df.dtypes[k] == int:
                values += f"""{v},"""
            else:
                # string values in the query should be in single qutation!
                values += f"""'{v}',"""
        # remove the last comma
        names = names[:-1]
        values = values[:-1]
        q = q + f""" ({names})""" + f""" VALUES({values})"""
        query_job = client.query(q)
        return {"status": "sucess", "data": data}
    return {"status": "failed"}

#Get Bigquery data
@app.route('/get_bigquery_data', methods=['GET'])       
def get_bigquery_data():
    client = bigquery.Client()

    query = f"""
    SELECT *
    FROM `{dataset}`
    """

    query_job = client.query(query)
    df = query_job.to_dataframe()
    
    df['time'] = df['time'].apply(lambda x: str(x) if pd.notnull(x) else None)
    
    return jsonify(df.to_dict('records'))

#Get current weather
@app.route('/get_actual_outdoor_weather', methods=['GET', 'POST'])
def get_actual_outdoor_weather():
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
    response = requests.get(url).json()
    response = response["list"][0]
    temperature = round(response["main"]["temp"], 1)
    humidity = response["main"]["humidity"]
    feels_like = response["main"]["feels_like"]
    icon = response["weather"][0]["icon"]
    description = response["weather"][0]["description"]
    wind = response["wind"]["speed"]
   
    return jsonify({"outdoor_temp": temperature, "outdoor_humidity": humidity, "outdoor_feels_like": feels_like, "description": description, "icon": icon, "wind": wind})

#Get weather forecast
@app.route('/get_weather_forecast', methods=['GET'])
def get_weather_forecast():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
    response = requests.get(url).json() 
    
    forecast_data = []
    for forecast in response["list"][1:]:
        forecast_dict = {}
        forecast_dict["hour"] = forecast["dt_txt"].split(" ")[1][:-3]
        forecast_dict["date"] = forecast["dt_txt"].split(" ")[0]
        forecast_dict["temperature"] = round(forecast["main"]["temp"])
        forecast_dict["icon"] = forecast["weather"][0]["icon"]
        forecast_dict["wind"] = forecast["wind"]["speed"]
        forecast_data.append(forecast_dict)

    return jsonify(forecast_data)


@app.route('/get_weather_forecast_day', methods=['GET'])
def get_weather_forecast_day():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
    response = requests.get(url).json() 

    forecasts_by_date = collections.defaultdict(list)
    for forecast in response["list"][1:]:
        date = forecast["dt_txt"].split(" ")[0]
        forecasts_by_date[date].append(forecast)

    max_temps = {}
    for date, forecasts in forecasts_by_date.items():
        max_temp = -float('inf')
        max_temp_icon = ""
        for forecast in forecasts:
            temperature = round(forecast["main"]["temp"])
            if temperature > max_temp:
                max_temp = temperature
                max_temp_icon = forecast["weather"][0]["icon"]
        max_temps[date] = {"max_temp": max_temp, "max_temp_icon": max_temp_icon}

    return jsonify(max_temps)

#Get GenAI weather advice
@app.route('/get_weather_advice', methods=['GET'])
def get_weather_advice():
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
    response = requests.get(url).json()
    response = response["list"][0]
    description = response["weather"][0]["description"]

    prompt = f"""Given the weather report: {description}, what advice should I give? 
        Please start by saying what the forecast is, followed by the advice. 
        In addition, please do not include any special characters in the advice, only letters. 
        For example, the character '=' should be written as equal(s) instead. 
        Lastly, be sure to only return one full sentence, not more."""

    response = OpenAI_client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=50,  
        temperature=0.5,  
        n=1,  
        stop=None  
    )
    generated_advice = response.choices[0].text.strip()
    return jsonify(f"{generated_advice}") #Today the weather forecast is {description},

#Google text to speech
@app.route('/get_text_to_speech_google', methods=['GET'])
def text_to_speech_google():
    text = request.args.get('text')

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code='en-IN',
        name='en-IN-Wavenet-A',
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16)

    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config)

    output_file='output.wav'
    
    with open(output_file, 'wb') as out:
        out.write(response.audio_content)

    return Response(response.audio_content, mimetype='audio/wav')

#Generate current weather image
@app.route('/image/current_weather', methods=['GET'])
def get_weather_image():

    #Get weather details
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
    response = requests.get(url).json()
    response = response["list"][0]

    #Get weather icon
    icon_code = response["weather"][0]["icon"]
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
    icon_response = requests.get(icon_url)
    icon_img = Image.open(BytesIO(icon_response.content)).resize((150, 150), Image.LANCZOS) #Icon image size

    #Create image
    img = Image.new('RGB', (320, 240), color=(0, 0, 0))  # Background & image size
    draw = ImageDraw.Draw(img)

    # Font load
    #font_large = ImageFont.truetype(font_path, 40)
    font_medium = ImageFont.truetype(font_path, 20)
    font_small = ImageFont.truetype(font_path, 14)

    # Outdoor weather information
    temp_str =  f"{round(response['main']['temp'], 1)} °C"
    humidity_str = f"Humidity: {response['main']['humidity']}%"
    wind_speed_str = f"Wind Speed: {response['wind']['speed']} m/s"

    # Text positions
    wind_speed_width = draw.textlength(wind_speed_str, font=font_small)

    temp_x = 200
    temp_y = (img.height - font_medium.size + 100) // 2

    icon_x = img.width - icon_img.width - 10
    icon_y = (img.height - icon_img.height - 50) // 2

    humidity_x = 10
    humidity_y = img.height - font_medium.size - 10

    wind_speed_x = img.width - wind_speed_width - 10
    wind_speed_y = img.height - font_medium.size - 10

    location_x = 10
    location_y = 50

    # Draw text and elements on the image
    draw.text((temp_x, temp_y), temp_str, font=font_medium, fill=(255, 255, 255))
    draw.text((humidity_x, humidity_y), humidity_str, font=font_small, fill=(255, 255, 255))
    draw.text((wind_speed_x, wind_speed_y), wind_speed_str, font=font_small, fill=(255, 255, 255))
    draw.text((location_x, location_y), location, font=font_medium, fill=(255, 255, 255))

    # Paste the icon image
    img.paste(icon_img, (icon_x, icon_y), icon_img)

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=False)

#Generate weather forecast image
@app.route('/image/weather_forecast', methods=['GET'])
def get_forecast_image():
    try:
        # Get weather details
        location = request.args.get('location', default='Lausanne', type=str)
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OW_API_KEY}&units=metric"
        response = requests.get(url).json()
        if response.get("cod") != "200":
            return jsonify({"error": "Failed to retrieve weather data"}), 500

        forecasts = response["list"]
        
        # Group forecasts by day and filter only daytime hours (6 AM to 6 PM)
        daily_forecasts = collections.defaultdict(list)
        daily_icons = collections.defaultdict(list)
        for forecast in forecasts:
            dt = datetime.fromtimestamp(forecast["dt"])
            if 6 <= dt.hour < 18:  # Filter for daytime hours
                date = dt.date()
                daily_forecasts[date].append(forecast["main"]["temp"])
                daily_icons[date].append(forecast["weather"][0]["icon"])
        
        # Get the highest temperature for each of the next 5 days
        max_temps = {}
        icons = {}
        current_date = datetime.now(pytz.timezone('Europe/Zurich')).date()
        for i in range(1, 6):
            day = current_date + timedelta(days=i)
            if day in daily_forecasts and daily_forecasts[day]:
                max_temps[day] = max(daily_forecasts[day])
                icons[day] = daily_icons[day][daily_forecasts[day].index(max_temps[day])]  # Get the icon for the max temp
            else:
                max_temps[day] = None
                icons[day] = None

        # Create image
        img = Image.new('RGB', (320, 240), color=(0, 0, 0))  # Background & image size
        draw = ImageDraw.Draw(img)

        # Use the full path to load the font
        font_large = ImageFont.truetype(font_path, 20)

        # Position elements
        x = 10
        y = 10
        y_spacing = 45

        for i, (day, max_temp) in enumerate(max_temps.items()):
            day_name = day.strftime('%A')
            temp_str = f"{round(max_temp, 1)} °C" if max_temp is not None else "N/A"
            
            # Position day and date
            draw.text((x, y + 10 + y_spacing * i), day_name, font=font_large, fill=(255, 255, 255))
            
            # Use the corresponding icon
            if icons[day] is not None:
                icon_code = icons[day]
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                icon_response = requests.get(icon_url)
                icon_img = Image.open(BytesIO(icon_response.content)).convert("RGBA")  # Convert to RGBA mode
                icon_img = icon_img.resize((60, 60), Image.LANCZOS)  # Resize the icon
                img.paste(icon_img, (x + 140, y - 10 + y_spacing * i), mask=icon_img)  # Use mask to paste with transparency
            else:
                draw.text((x + 140, y - 10 + y_spacing * i), "N/A", font=font_large, fill=(255, 255, 255))
            
            draw.text((x + 210, y + 10 + y_spacing * i), temp_str, font=font_large, fill=(255, 255, 255))  # Adjusted x_offset

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png', as_attachment=False)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Generte indoor weather image
@app.route('/image/indoor', methods=['GET'])
def create_image_with_logos():
    # Load the main image (where the logos will be pasted)
    main_img = Image.new('RGB', (320, 240), color = (0, 0, 0))

    # Load the logos
    humidity_logo = Image.open('humidity_logo.png') #Icon by justicon
    temperature_logo = Image.open('temperature_logo.png') #Icon by Freepik
    co2_logo = Image.open('co2_logo.png') #Icon by gungyoga04

    # Resize the logos
    humidity_logo = humidity_logo.resize((20, 20))
    temperature_logo = temperature_logo.resize((20, 20))
    co2_logo = co2_logo.resize((20, 20))

    # Paste the logos into the main image
    main_img.paste(temperature_logo, (80, 100))
    main_img.paste(humidity_logo, (80, 140))
    main_img.paste(co2_logo, (80, 180))

    # Save the image to a BytesIO object
    img_io = BytesIO()
    main_img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)




