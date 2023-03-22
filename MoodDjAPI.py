#Flask server that will handle all requests from the User interface (App or Browser). Acts as middle man between user and server

import flask
import ApiHelper as helper
import DB
import pickle
import spotipy
import random

application = flask.Flask(__name__)
ip = '192.168.137.48'
scopes = 'user-library-read playlist-modify-private playlist-modify-public user-read-email user-read-private'

redirect = 'http://'+ip+':5000/api/push_button'
config = {
    'user': 'api',
    'password': '',
    'host': '127.0.0.1', # IP address unless database is on local machine, then 127.0.0.1
    'database': 'mood_dj', # database name
    'port': '7983',
    'raise_on_warnings': True
    }

@application.route('/', methods=['GET', 'POST'])  # Home page, needed by Flask
def home():
    return"<h1>Hello World!<h1>"

@application.route('/api/print', methods=['GET', 'POST'])  # Test
def api_print():
    helper.check()
    return 'Printed'

@application.route('/api/push_button', methods=['GET', 'POST']) 
def api_pushbutton(): # Helper function for browser within app on mobile device
    return "<h1>Press the check button to continue and then retry the desired action<h1>"

@application.route('/api/login', methods=['GET', 'POST'])
def api_login(): # Takes input from mobile application/website and verifies login credentials
    arguments = flask.request.args
    name = arguments['name']
    passwd = arguments['passwd']
    cnx = DB.makeConnection(config)
    success = DB.getPass(cnx, name, passwd)
    if success:
        return 'Good'
    else:
        return 'Bad'

@application.route('/api/create_account', methods=['GET', 'POST'])
def api_createAccount(): # Takes input from mobile application/website and creates user account
    arguments = flask.request.args
    name = arguments['name']
    passwd = arguments['passwd']
    cnx = DB.makeConnection(config)
    users = DB.getUsers(cnx)
    if name in users:
        return 'Error_username'
    else:
        DB.addUser(cnx, (name, passwd))
    return 'Good'

@application.route('/api/authorizehelper', methods=['GET', 'POST'])
def api_authorizehelper(): # Generate a token to handle spotify requests
    arguments = flask.request.args
    code = arguments['code']
    name = arguments['name']
    displayName = helper.getToken(code, name, ip)
    cnx = DB.makeConnection(config)
    DB.insertSpot(cnx, displayName, name)
    return 'Token_Created' # may have to also return a string to close the webview

@application.route('/api/check_for_token', methods=['GET', 'POST'])
def api_checkForToken(): # Check for a token to handle spotify requests
    arguments = flask.request.args
    name = arguments['name']
    try:
        with open(name+'_tokens.data', 'rb') as filehandle:
            tokens = pickle.load(filehandle)
        tokens[0]['access'] = helper.refresh(tokens[0]['refresh'])
        with open(name+'_tokens.data', 'wb') as filehandle:
            pickle.dump(tokens, filehandle)
        sp = spotipy.Spotify(auth=tokens[0]['access'])
        
    except:
        return 'WebView'
    return 'Get_Songs'
     # Return a string saying that we need to open webview at this address

@application.route('/api/getSongs', methods=['GET', 'POST'])
def api_getSongs(): # Once request is sent from application/website calls DB function to pull songs
    arguments = flask.request.args
    name = arguments['name']
    try:
        with open(name+'_tokens.data', 'rb') as filehandle:
            tokens = pickle.load(filehandle)
        tokens = tokens[0]
        sp = spotipy.Spotify(auth=tokens['access'])
        
    except:
        return flask.redirect('https://accounts.spotify.com/authorize' +
                           '?response_type=code' +
                           '&client_id=1c5b495ed3644b4b94d7b71c613564e8'+
                           '&scope=' + scopes +
                           '&redirect_uri=' + redirect +
                           '&show_dialog=true')
     # Return a string saying that we need to open webview at this address
    info = []
    info = DB.getLikedSongs(sp)
    cnx = DB.makeConnection(config)
    DB.addToDB(cnx, info, name)
    return 'Done' # Return string saying everything went according to plan

@application.route('/api/create_playlist', methods=['GET', 'POST'])
def api_createPlaylist(): # Once request is sent from application/website calls DB function to generate a playlist and send it back to application/website
    arguments = flask.request.args
    mood = arguments['mood']
    limit = arguments['limit']
    username = arguments['name']
    limit = int(limit)
    cnx = DB.makeConnection(config)
    info = DB.getSongs(cnx, username, limit, mood)
    if limit >= len(info):
        limit = len(info)-1
    selected = random.sample(info, limit)
    return flask.jsonify(selected)

@application.route('/api/add_to_spotify', methods=['GET', 'POST'])
def api_addToSpotify():  #Once request is sent from application/website calls DB function to save playlist to Spotify account
    arguments = flask.request.args
    name = arguments['user']
    mood = arguments['mood']
    data = flask.request.get_json(force=True)
    with open(name+'_tokens.data', 'rb') as filehandle:
        tokens = pickle.load(filehandle)
    tokens[0]['access'] = helper.refresh(tokens[0]['refresh'])
    with open(name+'_tokens.data', 'wb') as filehandle:
        pickle.dump(tokens, filehandle)
    sp = spotipy.Spotify(auth=tokens[0]['access'])
    cnx = DB.makeConnection(config)
    
    ids =[]
    for i in data:
        ids.applicationend(i['id'])
    print(ids)
    sName = DB.getSpot(cnx, name)
    pId = DB.getPid(cnx, mood+'_id', name)
    if pId == 'null' or pId == None:
        p = sp.user_playlist_create(sName, "Mood DJ "+mood, public=False)
        pId = p['id']
        DB.insertPid(cnx, pId, mood+'_id', name)
        sp.user_playlist_add_tracks(sName, pId, ids)
    else:
        sp.user_playlist_replace_tracks(sName, pId, ids)
    print('Added')
    
    return 'Done'
    

application.run(host='0.0.0.0')
