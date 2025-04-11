import pandas as pd
from spotify_client import get_spotify_client
import time

sp = get_spotify_client()

def fetch_all_tracks():
    results = []

    # User's saved tracks
    saved_tracks = sp.current_user_saved_tracks(limit=50)
    while saved_tracks:
        for item in saved_tracks['items']:
            track = item['track']
            genre = fetch_artist_genre(track['artists'][0]['id'])
            results.append({
                'song': track['name'],
                'artist': track['artists'][0]['name'],
                'genre': genre if genre else 'Unknown',
                'url': track['external_urls']['spotify']
            })
        if saved_tracks['next']:
            saved_tracks = sp.next(saved_tracks)
        else:
            break

    # User's playlists
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        tracks = sp.playlist_tracks(playlist['id'], limit=100)
        while tracks:
            for item in tracks['items']:
                track = item['track']
                if track:
                    genre = fetch_artist_genre(track['artists'][0]['id'])
                    results.append({
                        'song': track['name'],
                        'artist': track['artists'][0]['name'],
                        'genre': genre if genre else 'Unknown',
                        'url': track['external_urls']['spotify']
                    })
            if tracks['next']:
                tracks = sp.next(tracks)
            else:
                break

    return pd.DataFrame(results)

def fetch_artist_genre(artist_id):
    artist = sp.artist(artist_id)
    return artist['genres'][0] if artist['genres'] else None

def create_playlists_by_genre(df):
    genres = df['genre'].unique()
    for genre in genres:
        filtered = df[df['genre'] == genre]
        if len(filtered) < 3:  # Optional threshold
            continue
        playlist = sp.user_playlist_create(user=sp.me()['id'], name=f"{genre} Collection", public=False)
        track_urls = filtered['url'].tolist()
        track_ids = [url.split("/")[-1] for url in track_urls]
        for i in range(0, len(track_ids), 100):
            sp.playlist_add_items(playlist_id=playlist['id'], items=track_ids[i:i+100])
        time.sleep(1)  # Respect rate limits