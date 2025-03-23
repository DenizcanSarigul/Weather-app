# WeatherApp

Welcome to our WeatherApp GitHub repository! Here you will find information on what to expect from our IoT weather station and how to use it. Our project consists of two main elements: an online dashboard for consulting various weather details and the M5 Stack IoT weather device.

## Dashboard

The link to access the dashboard is found at the top of the page, and the code is located in the `frontend` folder.


The dashboard is organized by containers and displays the following:
- Current date, location, and time
- Current weather in Lausanne & indoor values
- Forecast for the next three days
- Forecast for the day
- Boxplot of the outdoor temperature
- Weather frequencies
- Comparative line graph

![image](https://github.com/DenizcanSarigul/WeatherApp/assets/146003148/3b56ccc2-33fd-497b-8661-e48e5ed647e5)
#### Image extract of the dashboard


## IoT Device

The device is simple and user-friendly. When turned on, it brings the user to the main page, where one can find the indoor humidity rate, CO2 level, and temperature in Celsius. 

### Device Buttons
- **Left button**: Main page
- **Middle button**: Current weather in Lausanne
- **Right button**: Forecast for the next five days in Lausanne

### Integrated Alerts
- **Motion sensor alert**: Announces the weather when someone gets close to the device and suggests advice (e.g., what to wear).
- **Humidity alert**: Vibrates, shows a red light, and issues an audio warning when humidity levels fall below 40%.
- **Air Quality alert**: Vibrates, shows a red light, and issues an audio warning when CO2 levels become too high.

The code for the device can be found in the file `Main_m5stack`.

## Backend

The IoT device does not operate everything internally. For example, it sends back the indoor weather information to a BigQuery table in Google Cloud, which is used to display historical values in the Dashboard. Additionally, the IoT device receives information such as the current weather and forecast. The supporting code for the Service URL is found in the `backend` folder.


## Folder Structure

- **frontend**: Contains the code for the online dashboard.
- **backend**: Contains the code for handling backend operations and integrations.
- **Main_m5stack**: Contains the code for the M5 Stack IoT weather device.

## Links 

Our YouTube video : https://youtu.be/cjEizAL9uEA