# Imports
import pandas as pd
import matplotlib.pyplot as plt
from db_config import get_redis_connection
import secrets1
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import seaborn as seaborn
import seaborn.objects as seaborn_objects

# Album ID used (Guardians of the Galaxy)
GotG_PLAYLIST_ID = "37i9dQZF1DXatoD1BSWRau"

# Color codes for plotting data
red = '#ef4444'
green = '#84cc16'
orange = '#fb923c'
blue = '#22d3ee'
gray = '#475569'

class Spotify:

    def __init__(self,playlistID):
        
        self.client_creds_manager = SpotifyClientCredentials(client_id=secrets1.CLIENT_ID, client_secret=secrets1.CLIENT_SECRET)
        self.spotify = spotipy.Spotify(client_credentials_manager=self.client_creds_manager)
        self.playlist = self.spotify.playlist_tracks(playlist_id=playlistID)
        
    def getPopularityOfTracks(self):
        
        return [track['track']['popularity'] for track in self.playlist['items']]
    
    def getAveragePopularity(self):
        
        nonZeroPops = [pop for pop in self.getPopularityOfTracks() if pop!=0]
        averagePop = round(sum(nonZeroPops)/len(nonZeroPops)) if nonZeroPops else 0
        return averagePop
    
    def getPlaylistData(self):

        playlistData = []
        
        for track in self.playlist['items']:
            popularity = track['track']['popularity']
            
            if popularity == 0:
                popularity = self.getAveragePopularity()
                
            trackData = {
                "artist_name": track['track']['artists'][0]['name'],
                "track_name": track['track']['name'],
                "release_year": track['track']['album']['release_date'].split('-')[0],
                "duration_minutes": track['track']['duration_ms'] // 60000,
                "duration_seconds": (track['track']['duration_ms'] // 1000) % 60,
                "popularity": popularity,
                "track_id": track['track']['id']
            }
            
            playlistData.append(trackData)
        
        return playlistData

class Redis:

    def __init__(self):

        self.redisConnection = get_redis_connection()
        self.flushAllFromRedis()
    
    def insertDataIntoRedis(self,key,value):

        self.redisConnection.json().set(key,'.',json.dumps(value))
        
    def flushAllFromRedis(self):

        self.redisConnection.flushall()

    def getDataFromRedis(self,key):
        
        json_data = self.redisConnection.json().get(key)
        return json.loads(json_data)
    
    def keys(self):

        return self.redisConnection.keys()    

def main():
    
    spotify = Spotify(GotG_PLAYLIST_ID)
    playlistData = spotify.getPlaylistData()

    localRedis = Redis()

    for song in range(len(playlistData)):
        key = f"songs:{song}"
        localRedis.insertDataIntoRedis(key,playlistData[song])

    keys = localRedis.keys()
    
    redisData = []
    for key in keys:
        redisInstance = localRedis.getDataFromRedis(key)
        redisData.append(redisInstance)
    
    playlistDataFrame = pd.DataFrame().from_dict(redisData)
    
    processing1(playlistDataFrame)
    
    processing2(playlistDataFrame)
    
    processing3(playlistDataFrame)
    
    # Display the plot
    plt.show()
    
def processing1(df):
    # Displays Song's Popularity

    df['popularity'] = df['popularity'].astype(int)
    
    print("\n\t\t\t ##### Displays Song's Release Year #####\n")
    print(df.nlargest(10,'popularity')[['artist_name','track_name','popularity']].to_string(index=False))
    print("\n")

def processing2(df):
    # Displays Song's Release Year
    
    df['release_year'] = df['release_year'].astype(int)

    print("\t\t\t\t\t\t ##### Displays Song's Release Year #####\n")
    print(df.sort_values(by=['release_year'])[['artist_name','track_name','release_year']].to_string(index=False))

def processing3(df):
    # Plots the Amount of Songs From Each Individual Artist

    artist_counts = df['artist_name'].value_counts().nlargest(n=10)
    
    plt.figure(1)
    artist_counts.plot(kind='bar', figsize=(8, 10), color = orange)
    plt.xticks(rotation=30)
    plt.yticks(range(0,21,1))
    plt.title('Amount of Songs From Each Artist')
    plt.xlabel('Artist Names')
    plt.ylabel('Amount of Songs')
    
main()