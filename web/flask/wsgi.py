"""
this is meant to run locally on user end, fetch new results from available radiostations
functionality would include:
  - being able to host a wifi spot to gather credentials
  - use those to log into the provided network 
      - signal with lights if connection is successfull or not 
          -> if not spawn server again
  - upon login default profile of the radio station would be made, that can be adjusted by the user
  - after, it should fetch a radiostation
      - if there are saved radiostations those to play first, otherwise the last one in use
  - be influenced by the input from the knob
  - 
 when post request is sent and want to go back it actually sends post request again 
"""

# web/flask/wsgi.py
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from audio_player import AudioPlayer
from flask import Flask, render_template, request, jsonify, send_from_directory
from radio_api.lookup_radios import downloadRadiobrowserStats, check_stations_batch
from config import STATION_JSON_PATH, USER_SETTINGS_PATH, NOW_PLAYING_PATH, STATE_DIR

# create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    handlers=[
        RotatingFileHandler(
            'logs/app.log', maxBytes=5*1024*1024, backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# werkzeug 
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.DEBUG)
werkzeug_logger.propagate = False
werkzeug_logger.addHandler(
    RotatingFileHandler(
        'logs/werkzeug.log', maxBytes=5*1024*1024, backupCount=5
    )
)

app = Flask(__name__)
audio_player = AudioPlayer()


# --------------------------------------------------
# ----------------- HANDY FUNCY --------------------
# --------------------------------------------------


def load_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"file not found!!!! nothing in {json_path}")
        return[]
    
def save_user_settings(data):
    with open(USER_SETTINGS_PATH, 'w') as file:
        json.dump(data, file, indent=4)


# --------------------------------------------------
# ------------------- ENDPOINTS --------------------
# --------------------------------------------------

@app.route('/state/<filename>')
#                                                           #
#           endpoint to serve state files                   #
#                                                           #
def serve_state_file(filename):
    try:
        return send_from_directory(STATE_DIR, filename)
    except FileNotFoundError:
        return f"File '{filename}' not found in state directory.", 404
    


@app.route('/radios/play/<int:radio_num>', methods=['GET'])
def play_radio(radio_num): # maybe end point is not even needed, just trigger this..?
#                                                           #
#           endpoint to play radio stream                   #
#                                                           #
    stations = load_json(STATION_JSON_PATH)
    
    if radio_num < 1 or radio_num > len(stations):
        return f"radio station {radio_num} not found :(", 404
    
    station = stations[radio_num - 1]
    stream_url = station['url']
    station_uuid = station['stationuuid']

    try:
        # update user's last listened station
        user_settings = load_json(USER_SETTINGS_PATH)
        user_settings['User Settings'][0]['last_station_uuid'] = station_uuid
        save_user_settings(user_settings)
        
        # update now playing info
        now_playing = load_json(NOW_PLAYING_PATH)
        now_playing['current_station'].update({
            'name': station['name'],
            'stationuuid': station_uuid,
            'url': stream_url,
            'is_playing': True,
            'volume': user_settings['User Settings'][0].get('volume', 25)
        })
        
        # check for personal title in favorites
        # why tho...?
        for fav in user_settings.get('Favourite Stations', []):
            if fav['stationuuid'] == station_uuid:
                now_playing['current_station']['personal_title'] = fav.get('personal_title')
                break
        
        with open(NOW_PLAYING_PATH, 'w') as f:
            json.dump(now_playing, f, indent=4)
        
        # start playback
        audio_player.play_stream(stream_url)
        return '', 204
    except Exception as e:
        logger.error(f"Error playing radio: {e}")
        return f"Error playing the radio stream: {e}", 500


@app.route('/radios/play/uuid/<string:station_uuid>', methods=['GET'])
def play_radio_by_uuid(station_uuid):
    """
    endpoint to play a radio stream by its uuid
    this is useful when we have the uuid but not the index
    """
    stations = load_json(STATION_JSON_PATH)
    
    # find the station with the matching uuid
    station_index = -1
    for i, station in enumerate(stations):
        if station.get('stationuuid') == station_uuid:
            station_index = i
            break
    
    if station_index == -1:
        logger.error(f"station with uuid {station_uuid} not found")
        return f"radio station with uuid {station_uuid} not found :(", 404
    
    # use the existing play_radio function with the found index
    return play_radio(station_index + 1)  # add 1 since play_radio uses 1-based indexing


@app.route('/audio/stop', methods=['POST'])
def stop_playback():
    """endpoint to stop radio stream"""
    try:
        # stop playback
        audio_player.stop_stream()
        
        # update state
        now_playing = load_json(NOW_PLAYING_PATH)
        now_playing['current_station']['is_playing'] = False
        with open(NOW_PLAYING_PATH, 'w') as f:
            json.dump(now_playing, f, indent=4)
            
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"failed to stop playback: {e}")
        return jsonify({"error": str(e)}), 500





@app.route('/now_playing')
#                                                           #
#           endpoint to get now playing info                #
#                                                           #

def get_now_playing():
    try:
        now_playing = load_json(NOW_PLAYING_PATH)
        return jsonify(now_playing)
    except Exception as e:
        logger.error(f"failed to get now playing info: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/state/now_playing.json', methods=['POST'])
#                                                           #
#           endpoint to update now playing info             #
#                                                           #

def update_now_playing():
    try:
        data = request.get_json()
        with open(NOW_PLAYING_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.debug(f"failed to update now playing: {e}")
        return jsonify({"error": str(e)}), 500
        

@app.route('/add_favorite', methods=['POST'])
# BUG: Uncaught SyntaxError: '' string literal contains an unescaped line break
#      some station names are funky
#      when rendering names some characters can be dropped, what is really needed is . and ()

# TODO: check if after pressing "add" button the change to favorites list needs to be propagated into the json

def add_favorite():
#                                                           #
#   endpoint to add a radio station to the favorites list   #
#                                                           #

    data = request.json
    station_name = data.get('name')
    station_uuid = data.get('stationuuid')

    if not station_name or not station_uuid:
        return jsonify({"error": "Invalid data"}), 400

    user_settings = load_json(USER_SETTINGS_PATH)
    favorite_stations = user_settings.get("Favourite Stations", [])

    # check if station is already there
    for station in favorite_stations:
        if station.get('stationuuid') == station_uuid:
            logger.info(f"Station '{station_name}' is already in favorites.")
            return jsonify({"message": "Station already in favorites"}), 200 # TODO: to display via frontend

    new_station = {
        "name": station_name,
        "stationuuid": station_uuid,
        "personal_title": data.get('personal_title', ''), # in case front end fails
        "is_it_live": data.get('is_it_live', True)
    }
    
    favorite_stations.append(new_station)
    user_settings["Favourite Stations"] = favorite_stations
    save_user_settings(user_settings)

    logger.info(f"Station '{station_name}' added to favorites.")
    return jsonify({"message": "Station added to favorites"}), 201 # TODO: to display via frontend



@app.route('/check_stations_status', methods=['POST'])
#                                                           #
#      endpoint to check if favorite stations are live      # 
#                                                           #

def check_stations_status():
    """check if favorite stations are live"""
    try:
        # load user settings
        settings = load_json(USER_SETTINGS_PATH)
        favorite_stations = settings.get('Favourite Stations', [])
        
        # get station urls from station_scope.json
        stations = load_json(STATION_JSON_PATH)
        station_map = {station['stationuuid']: station for station in stations}
        
        # prepare stations for batch check
        stations_to_check = []
        for fav in favorite_stations:
            station = station_map.get(fav['stationuuid'])
            if station:
                stations_to_check.append(station)
        
        # check stations status in parallel
        status_results = check_stations_batch(stations_to_check)
        
        # update favorite stations status
        updated = False
        for station in settings['Favourite Stations']:
            new_status = status_results.get(station['stationuuid'])
            if new_status != station.get('is_it_live'):
                station['is_it_live'] = new_status
                updated = True
        
        # save updated settings if changed
        if updated:
            save_user_settings(settings)
        
        return jsonify(status_results)
        
    except Exception as e:
        logger.exception("error checking stations status")
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------
# ------------------- ADDRESSES --------------------
# --------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/radios')
def radios():
    # TODO: cache the result
    # TODO: load html and then display currently working stations
    # TODO: upon scrolling down to fetch more stations

    stations = load_json(STATION_JSON_PATH)
    
    # get global stats about working stations
    stats = downloadRadiobrowserStats()
    if stats:
        total_stations = stats.get('stations', 0)
        broken_stations = stats.get('stations_broken', 0)
        stations_working = total_stations - broken_stations
        logger.info(f"loaded {stations_working} working stations globally (out of {total_stations} total)") 
    else:
        # fallback to local counting if stats api fails
        stations_working = sum(1 for station in stations if station.get('lastcheckok') == 1)
        logger.info(f"loaded {stations_working} working stations from local cache") 

    return render_template('radios.html', stations_working=stations_working, stations=stations)



@app.route('/radios/<int:radio_num>', methods=['GET'])
def radio_details(radio_num):
    stations = load_json(STATION_JSON_PATH)

    if radio_num < 1 or radio_num > len(stations):
        return f"Radio station {radio_num} not found.", 404

    station = stations[radio_num - 1]
    clickcount = station.get('clickcount', 0)  # in case its missing would say no one listened

    return render_template('radio_details.html', radio_num=radio_num, station=station, clickcount=clickcount)


# potentially not needed, maybe only in frontend
@app.route('/radios/next', methods=['POST'])
def next_radio():
    # get current station info
    now_playing = load_json(NOW_PLAYING_PATH)
    stations = load_json(STATION_JSON_PATH)
    
    # find current station index
    current_uuid = now_playing['current_station'].get('stationuuid')
    current_index = 0
    
    for i, station in enumerate(stations):
        if station['stationuuid'] == current_uuid:
            current_index = i
            break
    
    # calculate next station index (wrap around to beginning if at end)
    next_index = (current_index + 1) % len(stations)
    
    while True:
        try:
            # use existing play_radio function to handle playback
            return play_radio(next_index + 1)  # add 1 since play_radio uses 1-based indexing
        except Exception as e:
            logger.warning(f"skipping station {next_index + 1} due to error: {e}")
            next_index = (next_index + 1) % len(stations)  # move to next station


@app.route('/radios/previous', methods=['POST'])
def previous_radio():
    # get current station info
    now_playing = load_json(NOW_PLAYING_PATH)
    logger.debug(f"loaded now playing info: {now_playing}")
    stations = load_json(STATION_JSON_PATH)
    logger.debug(f"loaded stations info: {stations}")
    
    # find current station index
    current_uuid = now_playing['current_station'].get('stationuuid')
    logger.debug(f"current station uuid: {current_uuid}")
    current_index = 0
    
    for i, station in enumerate(stations):
        if station['stationuuid'] == current_uuid:
            current_index = i
            logger.debug(f"found current station index: {current_index}")
            break
    
    # calculate previous station index (wrap around to end if at beginning)
    prev_index = (current_index - 1) % len(stations)
    
    while True:
        try:
            # use existing play_radio function to handle playback
            return play_radio(prev_index + 1)  # add 1 since play_radio uses 1-based indexing
        except Exception as e:
            error_message = str(e)
            if "Unknown mpeg MIME type" in error_message:
                logger.warning(f"skipping station {prev_index + 1} due to MIME type error")
                prev_index = (prev_index - 1) % len(stations)  # move to previous station
            else:
                logger.error(f"error changing to previous station: {e}")
                return jsonify({"error": str(e)}), 500

@app.route('/settings', methods=['GET', 'POST'])
def user_settings():
    try:
        with open(USER_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        settings = {
            "User Settings": [{"last_station": "", "volume": 25}],
        }

    if request.method == 'POST':
        try:
            data = request.get_json()
            logger.info(f"Received data: {data}")

            # volume update
            # BUG: somehow for a peculiar reason if volume bar is played with it deletes all favorite stations
            #  

            if 'volume' in data:
                volume = int(data['volume'])
                settings['User Settings'][0]['volume'] = volume
                logger.info(f"Volume updated to {volume}")

            # personal title is actually just a note
            if 'personalTitles' in data:
                for station_update in data['personalTitles']:
                    for station in settings['Favourite Stations']:
                        if station['stationuuid'] == station_update['stationuuid']:
                            station['personal_title'] = station_update['personalTitle']
                            logger.info(f"Updated personal title for station {station['name']}")
                            break

            # station deletion
            if 'deleteStations' in data:
                delete_uuids = data['deleteStations']
                original_length = len(settings['Favourite Stations'])
                settings['Favourite Stations'] = [
                    station for station in settings['Favourite Stations'] 
                    if station['stationuuid'] not in delete_uuids
                ]
                
                if len(settings['Favourite Stations']) < original_length:
                    logger.info(f"Deleted stations with UUIDs: {delete_uuids}")
                else:
                    logger.warning(f"Attempted to delete non-existent station UUIDs: {delete_uuids}")


            # save updated settings
            with open(USER_SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

            return jsonify({"status": "success"}) # TODO: to display via frontend nicely
        
        except Exception as e:
            logger.error(f"Error processing settings: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400

    return render_template('settings.html', settings=settings)


@app.route('/audio/settings', methods=['POST'])
def update_audio_settings():
    try:
        data = request.get_json()
        
        if 'volume' in data:
            volume = int(data['volume'])
            audio_player.set_volume(volume)
            
            # Update user settings file
            try:
                with open(USER_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                settings['User Settings'][0]['volume'] = volume
                with open(USER_SETTINGS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save volume setting: {e}")
            
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/weather/local')
def get_local_weather():
    """
    endpoint to get local weather data with enhanced location detection
    caches weather data to reduce api calls
    """
    import requests
    import time
    
    try:
        # check if we have cached weather data (cache for 15 minutes)
        cache_file = os.path.join(STATE_DIR, 'weather_cache.json')
        cache_duration = 15 * 60  # 15 minutes in seconds
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # check if cache is still valid
                if time.time() - cached_data.get('timestamp', 0) < cache_duration:
                    logger.debug("returning cached weather data")
                    return jsonify(cached_data['data'])
            except Exception as cache_error:
                logger.warning(f"failed to read weather cache: {cache_error}")
        
        # try to get location first using ipapi
        location_data = None
        try:
            location_response = requests.get('https://ipapi.co/json/', timeout=5)
            if location_response.status_code == 200:
                location_data = location_response.json()
        except Exception as location_error:
            logger.warning(f"failed to get location data: {location_error}")
        
        # determine location and weather query
        if location_data and location_data.get('city'):
            location = f"{location_data.get('city', 'unknown city')}, {location_data.get('country_name', 'unknown country')}"
            weather_query = location_data['city']
        else:
            # fallback to den haag
            location = "den haag, netherlands"
            weather_query = "den haag"
        
        # fetch weather data from wttr.in
        weather_response = requests.get(
            f'https://wttr.in/{weather_query}?format=j1',
            timeout=10
        )
        
        if weather_response.status_code != 200:
            raise Exception(f"weather api returned status {weather_response.status_code}")
        
        weather_data = weather_response.json()
        
        if not weather_data.get('current_condition') or not weather_data['current_condition']:
            raise Exception("invalid weather data structure")
        
        current_condition = weather_data['current_condition'][0]
        
        # prepare response data
        response_data = {
            'temperature': current_condition.get('temp_C'),
            'feels_like': current_condition.get('FeelsLikeC'),
            'humidity': current_condition.get('humidity'),
            'condition': current_condition.get('weatherDesc', [{}])[0].get('value', 'unknown'),
            'weather_code': current_condition.get('weatherCode'),
            'location': location.lower(),
            'timestamp': int(time.time())
        }
        
        # cache the response
        try:
            cache_data = {
                'data': response_data,
                'timestamp': time.time()
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=4)
        except Exception as cache_error:
            logger.warning(f"failed to cache weather data: {cache_error}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"error fetching weather data: {e}")
        
        # return fallback data
        fallback_data = {
            'temperature': '--',
            'feels_like': '--',
            'humidity': '--',
            'condition': 'data unavailable',
            'weather_code': '113',  # default to sunny
            'location': 'den haag, netherlands',
            'timestamp': int(time.time()),
            'error': str(e)
        }
        
        return jsonify(fallback_data), 500




if __name__ == "__main__":
    app.run()

