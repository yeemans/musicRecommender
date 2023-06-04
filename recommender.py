import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
from skimage import io
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import os
import sys
import requests
from collections import Counter
import random

clientId= sys.argv[1]
clientSecret = sys.argv[2]

def normalize(spotify_features_df): 
    scaled_features = MinMaxScaler().fit_transform([
    spotify_features_df['acousticness'].values,
    spotify_features_df['danceability'].values,
    spotify_features_df['duration_ms'].values,
    spotify_features_df['energy'].values,
    spotify_features_df['instrumentalness'].values,
    spotify_features_df['liveness'].values,
    spotify_features_df['loudness'].values,
    spotify_features_df['speechiness'].values,
    spotify_features_df['tempo'].values,
    spotify_features_df['valence'].values,
])
    spotify_features_df[['acousticness','danceability','duration_ms','energy','instrumentalness','liveness','loudness','speechiness','tempo','valence']] = scaled_features.T
    return spotify_features_df

def dropColumns(spotify_features_df): 
    #discarding the categorical and unnecessary features 
    spotify_features_df = spotify_features_df.drop('genre',axis = 1)
    spotify_features_df = spotify_features_df.drop('artist_name', axis = 1)
    spotify_features_df = spotify_features_df.drop('track_name', axis = 1)
    spotify_features_df = spotify_features_df.drop('popularity',axis = 1)
    spotify_features_df = spotify_features_df.drop('key', axis = 1)
    spotify_features_df = spotify_features_df.drop('mode', axis = 1)
    spotify_features_df = spotify_features_df.drop('time_signature', axis = 1)

    return spotify_features_df

def encodeGenreAndKey(spotify_features_df): 
    genre_OHE = pd.get_dummies(spotify_features_df.genre)
    key_OHE = pd.get_dummies(spotify_features_df.key)

    spotify_features_df = spotify_features_df.join(genre_OHE)
    spotify_features_df = spotify_features_df.join(key_OHE)
    return spotify_features_df

#creating the playlist dataframe with extended features using Spotify data
def generate_playlist_df(playlist, spotify_data):
    playlist_df = pd.DataFrame()

    for i, j in enumerate(playlist['tracks']['items']):
        playlist_df.loc[i, 'artist'] = j['track']['artists'][0]['name']
        playlist_df.loc[i, 'track_name'] = j['track']['name']
        playlist_df.loc[i, 'track_id'] = j['track']['id']
        playlist_df.loc[i, 'url'] = j['track']['album']['images'][1]['url']
        playlist_df.loc[i, 'date_added'] = j['added_at']

    playlist_df['date_added'] = pd.to_datetime(playlist_df['date_added'])  
    
    playlist_df = playlist_df[playlist_df['track_id'].isin(spotify_data['track_id'].values)].sort_values('date_added',ascending = False)

    return playlist_df 

def generate_playlist_vector(spotify_features, playlist_df):
    spotify_features_playlist = spotify_features[spotify_features['track_id'].isin(playlist_df['track_id'].values)]
    spotify_features_playlist = spotify_features_playlist.merge(playlist_df[['track_id','date_added']], on = 'track_id', how = 'inner')
    
    spotify_features_nonplaylist = spotify_features[~spotify_features['track_id'].isin(playlist_df['track_id'].values)]
    return spotify_features_playlist.sum(axis = 0), spotify_features_nonplaylist

def generate_recommendation(spotify_data, playlist_vector, nonplaylist_df):
    non_playlist = spotify_data[spotify_data['track_id'].isin(nonplaylist_df['track_id'].values)]
    non_playlist['sim'] = cosine_similarity(nonplaylist_df.drop(['track_id'], axis = 1).values, playlist_vector.drop(labels = 'track_id').values.reshape(1, -1))[:,0]
    non_playlist = non_playlist.sort_values('sim',ascending = False).iloc[:15]
    
    return non_playlist

def get_new_genre(playlist): 
    genreCounts = Counter()
    songCount = 0 

    for key in playlist.keys(): 
        if key not in genres: continue
        genreCounts[key] += playlist[key]
        songCount += playlist[key]
    
    newGenres = set(genres.copy()) # genres in this set make up less than 5% of the playlist 
    for key in playlist.keys(): 
        if genreCounts[key] / songCount >= 0.05: newGenres -= {key}

    # get a random genre from newGenres
    randomGenre = random.choice(tuple(newGenres))
    return randomGenre



def generate_other_genre_recommendation(spotify_data, playlist_vector, nonplaylist_df): 
    non_playlist = spotify_data[spotify_data['track_id'].isin(nonplaylist_df['track_id'].values)]

    randomGenre = get_new_genre(playlist_vector)
    print("random genre: " + randomGenre)
    non_playlist = non_playlist[non_playlist["genre"] == randomGenre]
    nonplaylist_df = nonplaylist_df[nonplaylist_df[randomGenre] == 1] # because of one-hot encoding

    print("non_playlist_df:")
    print([non_playlist.shape, nonplaylist_df.shape])

    non_playlist['sim'] = cosine_similarity(nonplaylist_df.drop(['track_id'], axis = 1).values, playlist_vector.drop(labels = 'track_id').values.reshape(1, -1))[:,0]
    non_playlist = non_playlist.sort_values('sim',ascending = False).iloc[:15]
    
    return non_playlist
   

data = pd.read_csv("SpotifyFeatures.csv")
spotify_features_df = data
genres = spotify_features_df.genre.unique()
spotify_features_df = normalize(spotify_features_df)
spotify_features_df = encodeGenreAndKey(spotify_features_df)
spotify_features_df = dropColumns(spotify_features_df)

access_token = "BQCJg2u_JOaJeKmvSElRmZy4PLiJ6un2AJ1az9Ukah--amidFNSmpQT9LayYNE6u-Tgud_K44CRx-1ueqZh53j0Td11nkVcSwecG6fzaPPbQUBQmjS0"
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}
BASE_URL = 'https://api.spotify.com/v1/'

# actual GET request with proper header
r = requests.get(BASE_URL + 'playlists/37i9dQZF1DXcBWIGoYBM5M', headers=headers)
json = r.json()
playlist_df = generate_playlist_df(json, data)
playlist_vector, nonplaylist_df = generate_playlist_vector(spotify_features_df, playlist_df)

# recommend
top15 = generate_recommendation(data, playlist_vector, nonplaylist_df)  
print(top15.head())

# recommend songs that are similar but have a different genre
top15 = generate_other_genre_recommendation(data, playlist_vector, nonplaylist_df)
print(top15)