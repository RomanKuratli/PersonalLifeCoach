from datetime import datetime

import requests

from utils import logging

owm_url = "https://api.openweathermap.org/data/2.5/weather"
CASHED_REQUEST = None  # Dict timestamp to json response
LOGGER = logging.get_logger("owm_client")


# date format for weather measures
def weather_measure_date_format(dt):
    return dt.strftime("%A, %-d. %B. %Y - %H:%M:%S")


def kelvin_to_celsius(kelvin):
    return round(kelvin - 273.15, 2)


def get_cashed_weather():
    global CASHED_REQUEST
    return CASHED_REQUEST


def get_weather(owm_key, city, alpha2_cd):
    global CASHED_REQUEST
    # openweathermap collects data only every 10 minutes
    if CASHED_REQUEST and city == CASHED_REQUEST["city"]:
        delta = datetime.now() - CASHED_REQUEST["timestamp"]
        if delta.days == 0 and delta.seconds > 600:
            return CASHED_REQUEST
    try:
        LOGGER.debug(f"Calling {owm_url}")
        params = {"APPID": owm_key, "q": f"{city},{alpha2_cd.lower()}"}
        response = requests.get(owm_url, params=params)
        if response.status_code == 200:
            json = response.json()
            tstamp = datetime.utcfromtimestamp(json["dt"])
            CASHED_REQUEST = {
                "city": city,
                "timestamp": tstamp,
                "timestamp_display": weather_measure_date_format(tstamp),
                "weather_id": json["weather"][0]["id"],
                "weather": json["weather"][0]["main"],
                "weather_desc": json["weather"][0]["description"],
                "icon": json["weather"][0]["icon"],
                "temp": kelvin_to_celsius(json["main"]["temp"]),
                "temp_min": kelvin_to_celsius(json["main"]["temp_min"]),
                "temp_max": kelvin_to_celsius(json["main"]["temp_max"])
            }
            return CASHED_REQUEST
        else:
            LOGGER.error(f"Request to {response.url} failed with status code {response.status_code}")
    except Exception as e:
        LOGGER.error(f"Error connecting to {owm_url}: {type(e)}")

