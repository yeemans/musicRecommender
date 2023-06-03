import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

clientCredentialsManager = SpotifyClientCredentials(client_id="ea0ac735771d4e4a83cc88d91b04cc14",
                                                    client_secret="5b43b3f4397149928983f1f9ac78d39c")
sp = spotipy.Spotify(client_credentials_manager = clientCredentialsManager)

playlist_link = "https://open.spotify.com/playlist/37i9dQZEVXbNG2KDcFcKOF?si=1333723a6eff4b7f"
playlist_URI = playlist_link.split("/")[-1].split("?")[0]
track_uris = [x["track"]["uri"] for x in sp.playlist_tracks(playlist_URI)["items"]]

print(sp.audio_features(track_uris)[0])