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

def generate_playlist_vector(spotify_features, playlist_df, weight_factor):
    spotify_features_playlist = spotify_features[spotify_features['track_id'].isin(playlist_df['track_id'].values)]
    spotify_features_playlist = spotify_features_playlist.merge(playlist_df[['track_id','date_added']], on = 'track_id', how = 'inner')
    
    spotify_features_nonplaylist = spotify_features[~spotify_features['track_id'].isin(playlist_df['track_id'].values)]
    return spotify_features_playlist.sum(axis = 0), spotify_features_nonplaylist

def generate_recommendation(spotify_data, playlist_vector, nonplaylist_df):

    non_playlist = spotify_data[spotify_data['track_id'].isin(nonplaylist_df['track_id'].values)]
    print([spotify_data.shape, non_playlist.shape])
    non_playlist['sim'] = cosine_similarity(nonplaylist_df.drop(['track_id'], axis = 1).values, playlist_vector.drop(labels = 'track_id').values.reshape(1, -1))[:,0]
    non_playlist = non_playlist.sort_values('sim',ascending = False).iloc[:15]
    
    print("non")
    print(non_playlist)
    return  non_playlist#_top15

data = pd.read_csv("SpotifyFeatures.csv")
spotify_features_df = data
spotify_features_df = normalize(spotify_features_df)
spotify_features_df = encodeGenreAndKey(spotify_features_df)
spotify_features_df = dropColumns(spotify_features_df)

access_token = "BQDjtWsioOkcg-dKL9zxhrAVP1OHkTCwZLPlRQo-D02JVdeWIEZi2qeY3sYspSJBr3mI8M7ySJWV7r-_UcvJuc0P966m8CX9w_ESlAFgdZ_1AR8i6t8"
headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}
# base URL of all Spotify API endpoints
BASE_URL = 'https://api.spotify.com/v1/'

# actual GET request with proper header
r = requests.get(BASE_URL + 'playlists/37i9dQZF1DX0kbJZpiYdZl', headers=headers)
json = r.json()
playlist_df = generate_playlist_df(json, data)
print(data.columns)
playlist_vector, nonplaylist_df = generate_playlist_vector(spotify_features_df, playlist_df, 1.2)
print(playlist_vector.shape)
print(nonplaylist_df.head())

# recs 
print([playlist_vector.shape, nonplaylist_df.shape])
top15 = generate_recommendation(data, playlist_vector, nonplaylist_df)  
top15.head()