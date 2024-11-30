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
from audio_player import AudioPlayer
from flask import Flask, render_template, request, jsonify, send_from_directory

from radio_api.lookup_radios import downloadRadiobrowserStats

app = Flask(__name__)
audio_player = AudioPlayer()
logging.basicConfig(level=logging.INFO)
 
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
        logging.error(f"file not found!!!! nothing in {json_path}")
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
    """
        endpoint to play radio stream

    """
    stations = load_json(STATION_JSON_PATH)
    
    if radio_num < 1 or radio_num > len(stations):
        return f"radio station {radio_num} not found :(", 404
    
    station = stations[radio_num - 1]
    stream_url = station['url']
    station_uuid = station['stationuuid']

    try: 
        with open(USER_SETTINGS_PATH, 'r', encoding='utf-8') as file:
                user_settings = json.load(file)

        user_settings['User Settings'][0]['last_station_uuid'] = station_uuid

        with open(USER_SETTINGS_PATH, 'w', encoding='utf-8') as file:
            json.dump(user_settings, file, indent=4)

        logging.info(f"updated user's last listened station to {station_uuid}")
    
    except Exception as e:
        print(f"error!!!!!!!!! while updating last_station: {e}")

    try:
        # update last played station
        audio_player.play_stream(stream_url)
        logging.info(f'trying to play stream: {stream_url}')
        return '', 204  # no content response, but success
    except Exception as e:
        return f"Error playing the radio stream: {e}", 500


@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    """
        endpoint to add a radio station to the favorites list.
        
    """
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
            logging.info(f"Station '{station_name}' is already in favorites.")
            return jsonify({"message": "Station already in favorites"}), 200 # TODO: to display via frontend

    new_station = {
        "name": station_name,
        "stationuuid": station_uuid,
        "personal_title": data.get('personal_title', ''),
        "is_it_live": data.get('is_it_live', True)
    }
    
    favorite_stations.append(new_station)
    user_settings["Favourite Stations"] = favorite_stations
    save_user_settings(user_settings)

    logging.info(f"Station '{station_name}' added to favorites.")
    return jsonify({"message": "Station added to favorites"}), 201 # TODO: to display via frontend


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

    stations = load_json(STATION_JSON_PATH)
    
    stations_working = len(stations) # not true, some are broken and its those are fetched
    logging.info(f"loaded {stations_working} stations") 

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
        logging.error(f"Error loading settings: {e}")
        settings = {
            "User Settings": [{"last_station": "", "volume": 25}],
            "Favourite Stations": []
        }

    if request.method == 'POST':
        try:
            data = request.get_json()
            logging.info(f"Received data: {data}")

            # volume update
            if 'volume' in data:
                volume = int(data['volume'])
                settings['User Settings'][0]['volume'] = volume
                logging.info(f"Volume updated to {volume}")

            # personal title is actually just a note
            if 'personalTitles' in data:
                for station_update in data['personalTitles']:
                    for station in settings['Favourite Stations']:
                        if station['stationuuid'] == station_update['stationuuid']:
                            station['personal_title'] = station_update['personalTitle']
                            logging.info(f"Updated personal title for station {station['name']}")
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
                    logging.info(f"Deleted stations with UUIDs: {delete_uuids}")
                else:
                    logging.warning(f"Attempted to delete non-existent station UUIDs: {delete_uuids}")


            # save updated settings
            with open(USER_SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

            return jsonify({"status": "success"}) # TODO: to display via frontend
        
        except Exception as e:
            logging.error(f"Error processing settings: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400

    return render_template('settings.html', settings=settings)






if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)

