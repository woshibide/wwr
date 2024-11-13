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
#


from flask import Flask
from flask import render_template

from radio_api.lookup_radios import downloadRadiobrowserStats

app = Flask(__name__)
app.run(debug=True)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/info')
def info():
    return '<h1>info</h1>'


@app.route('/radios')
def radios():
    # get the number of currently available working stations
    stats = downloadRadiobrowserStats()
    # TODO: cache the result
    # TODO: load html and then display currently working stations

    if stats and 'stations' and 'stations_broken' in stats:
        stations_working = stats['stations'] - stats['stations_broken']
    else:
        stations_working = 'UNKNOWN'

    return render_template('radios.html', stations_working=stations_working)


# should radios be numbered? some sort of conversion needs to take place
@app.route('/radios/<int:radio_num>')
def radio_details(radio_num):
    # return render template of a radio station info
    # return f'<h1>{radio_num}</h1><br>radio station'
    return render_template('radio_details.html', radio_num=radio_num)

@app.route('/settings')
def user_settings():
    # settings to be saved into a file and returned to user
    return render_template('settings.html')


