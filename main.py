import requests
from flask import Flask
from flask import make_response
from flask import jsonify
import time
import os
import werkzeug.datastructures

app = Flask(__name__)
app.config['secret_key'] = '999666999'
app.config['JSON_AS_ASCII'] = False

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
ALLOWED_APIKEY = os.environ.get('ALLOWED_API_KEY')

@app.route('/')
def root():
    return 'Hello World!'

@app.route('/ping')
def ping():
    return "pong!"

@app.route('/emoji/')
def emoji_lookup():
  emoji = {
    "Ash":":volcano:",
    "Clear":":sunny:",
    "Clouds":":cloud:",
    "Drizzle":":white_sun_rain_cloud:",
    "Dust":"??",
    "Fog":":foggy:",
    "Haze":"??",
    "Mist":":white_sun_rain_cloud:",
    "Rain":":cloud_rain:",
    "Sand":"??",
    "Smoke":":fire:",
    "Snow":":cloud_snow:",
    "Squall":":wind_blowing_face:",
    "Thunderstorm":":thunder_cloud_rain:",
    "Tornado":":cloud_tornado:"
  }
  return emoji
  
@app.route('/location/<location>')
def location_lookup(location):
  api = "https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={key}"
  url = api.format(location=location, key=GOOGLE_API_KEY)
  response = requests.get(url)
  js = response.json()
  
  lat = js["results"][0]["geometry"]["location"]["lat"]
  lon = js["results"][0]["geometry"]["location"]["lng"]
  location_name = js["results"][0]["formatted_address"]

  return jsonify(lat=lat, lon=lon, location_name=location_name)

@app.route('/weather/<location>/<auth>')
def weather_lookup(location, auth):
  if auth == ALLOWED_APIKEY:
      ljs = location_lookup(location).json
      location_name = ljs["location_name"]
      lat = ljs["lat"]
      lon = ljs["lon"]

      api = "https://api.openweathermap.org/data/2.5/onecall?units=imperial&lat={lat}&lon={lon}&appid={key}"
      url = api.format(lat=lat, lon=lon, key=OPENWEATHER_API_KEY)
      response = requests.get(url)
      js = response.json()

      temp_f = js["current"]["temp"]
      temp_c = round((js["current"]["temp"] - 32) / 1.8, 1)
      feels_like_f = js["current"]["feels_like"]
      feels_like_c = round((js["current"]["feels_like"] - 32) / 1.8, 1)
      humidity = js["current"]["humidity"]
      wind_mph = js["current"]["wind_speed"]
      wind_kph = round(js["current"]["wind_speed"] * 1.609, 1)
      wind_deg = js["current"]["wind_deg"]

      sunset = time.strftime("%H:%M", time.localtime(js["current"]["sunset"]))
      sunrise = time.strftime("%H:%M", time.localtime(js["current"]["sunrise"]))

      conditions = js["current"]["weather"][0]["main"]
      conditions_desc = js["current"]["weather"][0]["description"]
      edict = emoji_lookup()
      emoji = edict.get(conditions)

      discord = f"**Weather Report**: {location_name}\n**Temperature:** {temp_f}°F / {temp_c}°C (Feels like {feels_like_f}°F / {feels_like_c}°C)\n**Conditions:** {emoji} {conditions_desc} **Humidity:** {humidity}\n**Wind Speed:** {wind_mph}mph / {wind_kph}kph \n**Sunrise:** :sunrise:{sunrise} **Sunset:** :city_sunset:{sunset}"

      return jsonify(conditions=conditions,
                    conditions_desc=conditions_desc,
                    feels_like_f=feels_like_f,
                    feels_like_c=feels_like_c,
                    lat=lat,
                    lon=lon,
                    temp_f=temp_f,
                    temp_c=temp_c,
                    location_name=location_name,
                    sunset=sunset,
                    sunrise=sunrise,
                    emoji=emoji,
                    wind_mph=wind_mph,
                    wind_kph=wind_kph,
                    wind_deg=wind_deg,
                    discord=discord)

  return jsonify(error="Invalid API Key", discord="**INVALID API KEY**")

def main(request):
    with app.app_context():
        headers = werkzeug.datastructures.Headers()
        for key, value in request.headers.items():
            headers.add(key, value)
        with app.test_request_context(method=request.method, base_url=request.base_url, path=request.path, query_string=request.query_string, headers=headers, data=request.form):
            try:
                rv = app.preprocess_request()
                if rv is None:
                    rv = app.dispatch_request()
            except Exception as e:
                rv = app.handle_user_exception(e)
            response = app.make_response(rv)
            return app.process_response(response)
