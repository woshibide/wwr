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

app = Flask(__name__)
app.run(debug=True)

@app.route('/')
def index():
    return '<h1>WWR</h1><br><p>world wide radios</p>'


@app.route('/info')
def info():
    return '<h1>info</h1>'


@app.route('/radios')
def radios():
    return render_template('radios.html')


# should radios be numbered? some sort of conversion needs to take place
@app.route('/radios/<int:radio_num>')
def radio_details(radio_num):
    # return render template of a radio station infot
    # return f'<h1>{radio_num}</h1><br>radio station'
    return render_template('radio_details.html', radio_num=radio_num)

@app.route('/user/<path:user_id>/settings')
def user_settings(user_id):
    return f'these are the settings for {user_id}'


