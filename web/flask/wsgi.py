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

import os
import json
import logging
from logging.handlers import RotatingFileHandler
from audio_player import AudioPlayer
from flask import Flask, render_template, request, jsonify, send_from_directory

from radio_api.lookup_radios import downloadRadiobrowserStats, check_stations_batch

app = Flask(__name__)
audio_player = AudioPlayer()
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# this is temporary change for mac os development
# STATION_JSON_PATH = os.path.expanduser('~/wwr/web/flask/state/station_scope.json')
# USER_SETTINGS_PATH = os.path.expanduser('~/wwr/web/flask/state/user_settings.json')
STATION_JSON_PATH = os.path.expanduser('~/kabk/hacklab/dev/web/flask/state/station_scope.json')
USER_SETTINGS_PATH = os.path.expanduser('~/kabk/hacklab/dev/web/flask/state/user_settings.json')
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state')

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
def serve_state_file(filename):
    try:
        return send_from_directory(STATE_DIR, filename)
    except FileNotFoundError:
        return f"File '{filename}' not found in state directory.", 404
    

@app.route('/radios/play/<int:radio_num>', methods=['GET'])
def play_radio(radio_num):
#                                                           #
#   endpoint to play radio stream                           #
#                                                           #
    stations = load_json(STATION_JSON_PATH)
    
    if radio_num < 1 or radio_num > len(stations):
        return f"radio station {radio_num} not found :(", 404
    
    station = stations[radio_num - 1]
    stream_url = station['url']
    station_uuid = station['stationuuid']

    try: 
        with open(USER_SETTINGS_PATH, 'r', encoding='utf-8') as file:
                user_settings = json.load(file)

        # Get volume from user settings
        volume = user_settings['User Settings'][0].get('volume', 25)
        
        user_settings['User Settings'][0]['last_station_uuid'] = station_uuid

        with open(USER_SETTINGS_PATH, 'w', encoding='utf-8') as file:
            json.dump(user_settings, file, indent=4)

        logger.info(f"updated user's last listened station to {station_uuid}")
    
    except Exception as e:
        logger.error(f"error while updating last_station: {e}")
        volume = 25  # default volume if settings can't be read

    try:
        # Play stream with volume from settings
        audio_player.play_stream(stream_url, volume=volume)
        logger.info(f'trying to play stream: {stream_url} with volume {volume}')
        return '', 204
    except Exception as e:
        return f"Error playing the radio stream: {e}", 500


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
        "personal_title": data.get('personal_title', ''),
        "is_it_live": data.get('is_it_live', True) # TODO: dynamically check if station is live
    }
    
    favorite_stations.append(new_station)
    user_settings["Favourite Stations"] = favorite_stations
    save_user_settings(user_settings)

    logger.info(f"Station '{station_name}' added to favorites.")
    return jsonify({"message": "Station added to favorites"}), 201 # TODO: to display via frontend


@app.route('/check_stations_status', methods=['POST'])
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


if __name__ == "__main__":
    app.run()

