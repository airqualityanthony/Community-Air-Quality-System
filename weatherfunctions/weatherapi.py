import requests
import json

def get_weather(lat, lon,api_key):
    url = "https://api.tomorrow.io/v4/weather/realtime?location={lat},{lon}&apikey={api_key}".format()

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    res_json = json.loads(response.text)
    return res_json
