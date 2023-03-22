# Malcolm Sykes
# 3/29/2020
# Project: Mood Dj
# This program is using the Spotify API via a python library called Spotipy.
# It requests access to a user's Spotify account and grabs the songs from their
# liked songs playlist along with the song's attributes. It then connects to a 
# database where it stores the information in.
#NOTICE: Anywhere you see "sys.stdout.write", this is for piping output to the parent Java program that calls this script

import sys
import pickle
import numpy as np
import pandas as pd
import NNet_hidden2
import mysql.connector


def getLikedSongs(sp):  # Get all the songs in a user's Liked Songs playlist including artist name and all Spotify attributes 
    sys.stdout.write("Getting songs from Spotify...\n")
    sys.stdout.flush()
    songs = []
    count = 0 # To track progress
    punc = "!\"#%'()*+,/:;<=>?[\]^_`{|}~“”" # All punctuation we want to get rid of for sql queries to work
    table = str.maketrans('', '', punc)

    results = sp.current_user_saved_tracks(limit=20, offset=0) # Gets the first 20(max) songs 
    tracks = results
    for i in tracks['items']: # Loops through the 20 songs we just got
        tName = i['track']['name'].translate(table) # Takes unwanted punctuation out of the track name
        aName = i['track']['artists'][0]['name'].translate(table) # Takes unwanted punctuation out of the author name
        feat = sp.audio_features(i['track']['id'])[0] # Gets the Spotify audio features(attributes) for the song
        feat.update([('track', tName) , ('artist', aName)])
        songs.append(feat) # Adds track name, artist name, and song attributes to a data structure(in this case a list)
        count += 1
    sys.stdout.write(str(count) + '\n')
    sys.stdout.flush()
    while tracks['next']: # Continue to grab the next 20 songs until there are no more (and/or until it reaches a max) and repeats above steps
        tracks = sp.next(tracks)
        for i in tracks['items']:
            tName = i['track']['name'].translate(table)
            aName = i['track']['artists'][0]['name'].translate(table)
            feat = sp.audio_features(i['track']['id'])[0]
            feat.update([('track', tName) , ('artist', aName)])
            songs.append(feat)
            count += 1
        sys.stdout.write(str(count) + '\n')
        sys.stdout.flush()
    sys.stdout.write("Found " + str(count) + " songs\n")
    sys.stdout.flush()
    return songs

def getPredict(x):
    with open('NNBest.data', 'rb') as filehandle:
        # read the data as binary data stream
        NN = pickle.load(filehandle)
    return NN.predict(x)
    
def makeConnection(credentials): # Connect to database
    return mysql.connector.connect(**credentials)

def addToDB(cnx, info, username): #Adds all songs, attributes, and artists to the appropriate tables in the database
    sys.stdout.write("Adding to database...\n")
    sys.stdout.flush()
    frame = pd.DataFrame.from_dict(info) # Convert the list data structure from getLikedSongs to a dataframe for ease of use
    x = frame.drop(['tempo','mode', 'key', 'loudness', 'speechiness', 'valence', 'instrumentalness', 'type', 'id', 'uri', 'track_href', 'analysis_url', 'duration_ms', 'time_signature', 'track', 'artist'], axis=1)
    X = x.values
    X = X/np.amax(X, axis=0)
    predictions = getPredict(X)
    frame['Chill'] = predictions[0][0]
    frame['Happy'] = predictions[0][1]
    frame['Party'] = predictions[0][2]
    frame['Sad'] = predictions[0][3]
    frame['Workout'] = predictions[0][4]
    for i in range(1,len(predictions)):
        frame['Chill'][i] = predictions[i][0]
        frame['Happy'][i] = predictions[i][1]
        frame['Party'][i] = predictions[i][2]
        frame['Sad'][i] = predictions[i][3]
        frame['Workout'][i] = predictions[i][4]
    count = 0 # Track progress
    for index, song in frame.iterrows():
        insertArtist(song["artist"], cnx) # Put artist in the artists table
        artID = int(get_aID(song["artist"], cnx))
        # Get all info for the track in one place
        recordTuple = (song["track"], song["id"], round(song["danceability"], 9), round(song["energy"], 9),
                    song["key"], round(song["loudness"], 9), song["mode"], round(song["speechiness"], 9),
                    round(song["acousticness"], 9), round(song["liveness"], 9), round(song["valence"], 9),
                    round(song["tempo"], 4), song["Chill"], song["Happy"], song["Party"], song["Sad"], song["Workout"], artID)
        insertTrack(recordTuple, cnx) # Put track info in the tracks table
        trackID = int(get_tID(song["id"], cnx))
        if not checkFav(username, trackID, cnx):
            insertFav((username, trackID), cnx)
        count += 1
        if count % 50 == 0:
            sys.stdout.write(str(count) + '\n')
            sys.stdout.flush()

def insertArtist(value, cnx):  # Inserts the artist info into the artists table, ignoring duplicates
    try:
        insert_query = "INSERT IGNORE INTO artist (artist_name) VALUES ('" + value + "');" # SQL insert command
        cursor = cnx.cursor()
        cursor.execute(insert_query) # Run the command on database
        cnx.commit()
        cursor.close()

    except mysql.connector.Error as error: # If we get an error other than "Duplicate entry" print it (The same artist name is expected multiple times)
        err = ("{}".format(error)).split()
        if(err[1] != 'Duplicate'):
            print("Failed to insert record into artist table {}".format(error))

def insertTrack(values, cnx):  # Inserts the track info into the tracks table, ignoring duplicates
    try:
        # SQL insert query (%s is a place holder for a value to be specified later)
        insert_query = """INSERT IGNORE INTO track (track_name, spotify_id, danceability, energy, 
                          song_key, loudness, mode, speechiness, acousticness, liveness, valence, 
                          tempo, chill_predict, happy_predict, party_predict, sad_predict, workout_predict, artist_id) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        cursor = cnx.cursor()
        cursor.execute(insert_query, values) # Run the command and fill in %s with actual values
        cnx.commit()
        cursor.close()

    except mysql.connector.Error as error:
        err = ("{}".format(error)).split()
        if(err[1] != 'Duplicate'):
            print("Failed to insert record into track table {}".format(error))

def insertFav(values, cnx):  # Associates tracks with the user who likes them
    try:
        # SQL insert query (%s is a place holder for a value to be specified later)
        insert_query = "INSERT INTO favorites (user_name, track_id) VALUES (%s, %s);"
        cursor = cnx.cursor()
        cursor.execute(insert_query, values) # Run the command and fill in %s with actual values
        cnx.commit()
        cursor.close()

    except mysql.connector.Error as error:
        err = ("{}".format(error)).split()
        if(err[1] != 'Duplicate'):
            print("Failed to insert record into favorites table {}".format(error))

def get_aID(name, cnx):  # Gets the artist ID in order to link songs to them in the tracks table
    try:
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select artist_id from artist where artist_name = '" + name + "';" # SQL command to get the id for an artist
        cursor.execute(sql_select_query) # Run the command
        record = cursor.fetchall() # Get all results of the query (Should only be one)
        for row in record:
            return row[0]
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))

def get_tID(sid, cnx):  # Gets the track ID
    try:
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select track_id from track where spotify_id = '" + sid + "';" # SQL command to get the id for an artist
        cursor.execute(sql_select_query) # Run the command
        record = cursor.fetchall() # Get all results of the query (Should only be one)
        for row in record:
            return row[0]
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))

def checkFav(username, tid, cnx):  # Verifies if a track is already associated with a user
    try:
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select track_id from favorites where track_id = %s AND user_name = %s;" # SQL command to get the id for an artist
        cursor.execute(sql_select_query, (tid, username)) # Run the command
        record = cursor.fetchall() # Get all results of the query (Should only be one)
        if record == None:
            return False
        for row in record:
            return True
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))

def getUsers(cnx):  # Gets a list of Users
    users = []
    try:
        # If the user already exists, return the Users_id
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select user_name from user;" # SQL command to get the song_num for a song
        cursor.execute(sql_select_query) # Run the command
        record = cursor.fetchall() # Get all results of the query
        if record == None:
            return users
        for row in record:
            users.append(row[0])
        return users

    except mysql.connector.Error as error:
        print("Failed to get record from MySQL user table: {}".format(error))

def getPass(cnx, username, passwrd): # Checks if password entered and password stored in DB Match 
    try:
        # If the user already exists, return the Users_id
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select user_pass from user where user_name = '" + username + "';" # SQL command to get the song_num for a song
        cursor.execute(sql_select_query) # Run the command
        record = cursor.fetchall() # Get all results of the query
        if record == None or record == []: # If the password saved in DB is blank or empty
            return False
        if record[0][0] == passwrd: # If passwords match
            return True
        return False

    except mysql.connector.Error as error:
        print("Failed to get record from MySQL user table: {}".format(error))

def addUser(cnx, values): # Adds new User account to DB
    try:
        insert_query = "INSERT INTO user (user_name, user_pass) VALUES (%s, %s);" # SQL insert command
        cursor = cnx.cursor()
        cursor.execute(insert_query, values) # Run the command on database
        cnx.commit()
        cursor.close()
    except mysql.connector.Error as error: # If we get an error other than "Duplicate entry" print it (The same artist name is expected multiple times)
        err = ("{}".format(error)).split()
        if(err[1] != 'Duplicate'):
            print("Failed to insert record into user table {}".format(error))

def getSongs(cnx, username, limit, mood): # Gets a list of songs that satisfy the mood and playlist size limit
    songs = []
    try:
        cursor = cnx.cursor(buffered=True)
        if mood == 'happy':
            sql_select_query = """SELECT artist_name, track_name, spotify_id FROM favorites JOIN track USING(track_id)
                                 JOIN artist USING(artist_id) WHERE user_name = '""" + username + """'  
                                 and valence > .5 and happy_predict > .2 order by valence desc;""" # SQL command to get the song_num for a song
        elif mood == 'sad':
            sql_select_query = """SELECT artist_name, track_name, spotify_id FROM 
                                (SELECT artist_name, track_name, spotify_id, acousticness, liveness, energy, valence 
                                FROM favorites JOIN track USING(track_id) JOIN artist USING(artist_id) 
                                WHERE user_name = %s AND predict = 0 AND energy < .6 AND liveness < .2 AND acousticness > .1 
                                ORDER BY VALENCE) sad WHERE liveness < .1 OR valence < .61 LIMIT %s;""" # SQL command to get the song_num for a song
        elif mood == 'party':
            sql_select_query = """SELECT artist_name, track_name, spotify_id FROM favorites JOIN track USING(track_id) 
                                JOIN artist USING(artist_id) WHERE user_name = %s AND energy > .75 AND danceability > .75
                                ORDER by danceability desc, energy desc LIMIT %s;""" # SQL command to get the song_num for a song
        else:
            sql_select_query = """SELECT artist_name, track_name, spotify_id FROM favorites JOIN track USING(track_id) 
                                JOIN artist USING(artist_id) WHERE user_name = %s LIMIT %s;""" # SQL command to get the song_num for a song
        
        cursor.execute(sql_select_query)
        #cursor.execute(sql_select_query, (username, limit)) # Run the command
        record = cursor.fetchall() # Get all results of the query
        for row in record:
            songs.append(row)
        return songs

    except mysql.connector.Error as error:
        print("Failed to get record from MySQL user table: {}".format(error))

def insertSpot(cnx, sname, username): # Adds user's spotify username to the user's entry
    try:
        insert_query = "UPDATE user SET spotify_name = %s WHERE user_name = %s;" # SQL insert command
        cursor = cnx.cursor()
        cursor.execute(insert_query, (sname, username)) # Run the command on database
        cnx.commit()
        cursor.close()

    except mysql.connector.Error as error: # If we get an error other than "Duplicate entry" print it (The same artist name is expected multiple times)
        err = ("{}".format(error)).split()
        if(err[1] != 'Duplicate'):
            print("Failed to insert record into user table {}".format(error))

def getSpot(cnx, username): # Gets user's spotify name
    try:
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select spotify_name from user WHERE user_name = '" + str(username) + "';" # SQL command to get the song_num for a song
        cursor.execute(sql_select_query) # Run the command
        record = cursor.fetchall() # Get all results of the query
        if record == None or record == []:
            return None
        for row in record:
            return row[0]

    except mysql.connector.Error as error:
        print("Failed to get record from MySQL user table: {}".format(error)) 

def getPid(cnx, col, username): # Gets the playlist ID for the playlist we will be saving to as to not infinitely generate playlists. Returns None if there is no playlist associated with the mood
    try:
        cursor = cnx.cursor(buffered=True)
        sql_select_query = "select " + col + " from user WHERE user_name = '" + username + "';" # SQL command to get the song_num for a song
        cursor.execute(sql_select_query) # Run the command
        record = cursor.fetchall() # Get all results of the query
        if record == None:
            return None
        for row in record:
            return row[0]

    except mysql.connector.Error as error:
        print("Failed to get record from MySQL user table: {}".format(error))

def insertPid(cnx, pId, col, user): # Adds the playlist ID for the Playlist that was generated as to keep track of it
    try:
        insert_query = "UPDATE user SET " + col + " = %s WHERE user_name = %s;" # SQL insert command
        cursor = cnx.cursor()
        cursor.execute(insert_query, (pId, user)) # Run the command on database
        cnx.commit()
        cursor.close()

    except mysql.connector.Error as error: # If we get an error other than "Duplicate entry" print it (The same artist name is expected multiple times)
        err = ("{}".format(error)).split()
        if(err[1] != 'Duplicate'):
            print("Failed to insert record into user table {}".format(error))
