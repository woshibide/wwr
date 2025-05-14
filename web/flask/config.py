import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATION_JSON_PATH = os.path.expanduser('~/kabk/radio/dev/web/flask/state/station_scope.json')
USER_SETTINGS_PATH = os.path.expanduser('~/kabk/radio/dev/web/flask/state/user_settings.json')
# STATION_JSON_PATH = os.path.expanduser('~/wwr/web/flask/state/station_scope.json')
# USER_SETTINGS_PATH = os.path.expanduser('~/wwr/web/flask/state/user_settings.json')

STATE_DIR = os.path.join(BASE_DIR, 'state')
NOW_PLAYING_PATH = os.path.join(STATE_DIR, 'now_playing.json')