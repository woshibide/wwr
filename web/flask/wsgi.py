# this is meant to run locally on user end, fetch new results from available radiostations
# functionality would include:
#   - being able to host a wifi spot to gather credentials
#   - use those to log into the provided network 
#       - signal with lights if connection is successfull or not 
#           -> if not spawn server again
#   - upon login default profile of the radio station would be made, that can be adjusted by the user
#   - after, it should fetch a radiostation
#       - if there are saved radiostations those to play first, otherwise the last one in use
#   - be influenced by the input from the knob
#   - 
##  when post request is sent and want to go back it actually sends post request again 

import os
import json
import logging
from flask import Flask, render_template, request, jsonify

from radio_api.lookup_radios import downloadRadiobrowserStats
from audio_player import AudioPlayer

app = Flask(__name__)
audio_player = AudioPlayer()
 
logging.basicConfig(level=logging.INFO)

# STATION_JSON_PATH = os.path.expanduser('~/wwr/web/flask/state/station_scope.json')
# USER_SETTINGS_PATH = os.path.expanduser('~/wwr/web/flask/state/user_settings.json')

# this is temporary change for mac os development
STATION_JSON_PATH = os.path.expanduser('~/kabk/hacklab/dev/web/flask/state/station_scope.json')
USER_SETTINGS_PATH = os.path.expanduser('~/kabk/hacklab/dev/web/flask/state/user_settings.json')


def load_stations_from_json():
    try:
        with open(STATION_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"file not found!!!! nothing in {STATION_JSON_PATH}")
        return []

def load_user_settings():
    try: 
        with open(USER_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"file not found!!!! nothing in {STATION_JSON_PATH}")
        return []



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/info')
def info():
    return '<h1>info</h1>'


@app.route('/radios')
def radios():
    # TODO: cache the result
    # TODO: load html and then display currently working stations

    stations = load_stations_from_json()

    stations_working = len(stations) # not true, some are broken
    logging.info(f"loaded {stations_working} stations") 

    return render_template('radios.html', stations_working=stations_working, stations=stations)

@app.route('/radios/<int:radio_num>', methods=['GET'])
def radio_details(radio_num):
    stations = load_stations_from_json()

    if radio_num < 1 or radio_num > len(stations):
        return f"Radio station {radio_num} not found.", 404

    station = stations[radio_num - 1]
    clickcount = station.get('clickcount', 0)  # in case its missing would say no one listened

    return render_template('radio_details.html', radio_num=radio_num, station=station, clickcount=clickcount)


@app.route('/radios/play/<int:radio_num>', methods=['GET'])
def play_radio(radio_num):
    stations = load_stations_from_json()
    
    if radio_num < 1 or radio_num > len(stations):
        return f"Radio station {radio_num} not found.", 404
    
    station = stations[radio_num - 1]
    stream_url = station['url']

    try:
        # Use the AudioPlayer instance to play the stream
        audio_player.play_stream(stream_url)
        print(f'trying to play stream url: {stream_url}')
        return '', 204  # No content response, successful
    except Exception as e:
        return f"Error playing the radio stream: {e}", 500
    



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

            # Handle volume update
            if 'volume' in data:
                volume = int(data['volume'])
                settings['User Settings'][0]['volume'] = volume

            # Handle personal title update
            if 'personalTitles' in data:
                for station_update in data['personalTitles']:
                    for station in settings['Favourite Stations']:
                        if station['stationuuid'] == station_update['stationuuid']:
                            station['personal_title'] = station_update['personalTitle']
                            break

            # Save updated settings
            with open(USER_SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

            return jsonify({"status": "success"})
        
        except Exception as e:
            logging.error(f"Error processing settings: {e}")
            return jsonify({"status": "error", "message": str(e)}), 400

    return render_template('settings.html', settings=settings)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)

