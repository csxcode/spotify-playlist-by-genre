import pandas as pd
from spotify_client import get_spotify_client
import time

sp = get_spotify_client()

def fetch_all_tracks():
    print("Starting to fetch all tracks...")
    results = []
    track_count = 0

    # User's saved tracks
    print("Fetching your saved/liked tracks...")
    saved_tracks = sp.current_user_saved_tracks(limit=50)
    saved_count = 0
    while saved_tracks:
        for item in saved_tracks['items']:
            track = item['track']
            print(f"Processing: {track['name']} by {track['artists'][0]['name']}")
            genre = fetch_artist_genre(track['artists'][0]['id'])
            results.append({
                'song': track['name'],
                'artist': track['artists'][0]['name'],
                'genre': genre if genre else 'Unknown',
                'url': track['external_urls']['spotify']
            })
            saved_count += 1
        if saved_tracks['next']:
            print(f"Processed {saved_count} liked tracks so far, fetching more...")
            saved_tracks = sp.next(saved_tracks)
        else:
            break
    
    print(f"Completed processing {saved_count} liked tracks.")

    # User's playlists
    print("\nFetching tracks from your playlists...")
    playlists = sp.current_user_playlists()
    playlist_count = 0
    for playlist in playlists['items']:
        playlist_count += 1
        print(f"\nProcessing playlist {playlist_count}/{len(playlists['items'])}: {playlist['name']}")
        tracks = sp.playlist_tracks(playlist['id'], limit=100)
        playlist_track_count = 0
        while tracks:
            for item in tracks['items']:
                track = item['track']
                if track:
                    print(f"Processing: {track['name']} by {track['artists'][0]['name']}")
                    genre = fetch_artist_genre(track['artists'][0]['id'])
                    results.append({
                        'song': track['name'],
                        'artist': track['artists'][0]['name'],
                        'genre': genre if genre else 'Unknown',
                        'url': track['external_urls']['spotify']
                    })
                    playlist_track_count += 1
                    track_count += 1
            if tracks['next']:
                print(f"Processed {playlist_track_count} tracks in this playlist so far, fetching more...")
                tracks = sp.next(tracks)
            else:
                break
        print(f"Completed processing {playlist_track_count} tracks from playlist: {playlist['name']}")

    print(f"\nFinished processing a total of {len(results)} tracks.")
    return pd.DataFrame(results)

def fetch_artist_genre(artist_id):
    artist = sp.artist(artist_id)
    return artist['genres'][0] if artist['genres'] else None

def create_playlists_by_genre(df):
    print("\nStarting to create playlists by genre...")
    playlist_prefix = "[Auto]"
    genres = df['genre'].unique()
    print(f"Found {len(genres)} unique genres in your music.")
    
    created_count = 0
    skipped_count = 0
    
    for i, genre in enumerate(genres):
        print(f"\nProcessing genre {i+1}/{len(genres)}: {genre}")
        filtered = df[df['genre'] == genre]
        print(f"Found {len(filtered)} songs in the '{genre}' genre")
        
        if len(filtered) < 3:  # Optional threshold
            print(f"Excluded genre '{genre}' with only {len(filtered)} songs (below threshold of 3):")
            for _, row in filtered.iterrows():
                print(f"  - {row['song']} by {row['artist']}")
            skipped_count += 1
            continue
            
        print(f"Creating playlist: {playlist_prefix} {genre} Collection")
        playlist = sp.user_playlist_create(user=sp.me()['id'], name=f"{playlist_prefix} {genre} Collection", public=False)
        track_urls = filtered['url'].tolist()
        track_ids = [url.split("/")[-1] for url in track_urls]
        
        chunks = (len(track_ids) + 99) // 100  # Calculate number of chunks
        for i in range(0, len(track_ids), 100):
            chunk_end = min(i+100, len(track_ids))
            print(f"Adding tracks {i+1}-{chunk_end} of {len(track_ids)} to playlist...")
            sp.playlist_add_items(playlist_id=playlist['id'], items=track_ids[i:i+100])
        
        print(f"Successfully created playlist for '{genre}' with {len(track_ids)} tracks")
        created_count += 1
        time.sleep(1)  # Respect rate limits
    
    print(f"\nPlaylist creation complete: Created {created_count} playlists, skipped {skipped_count} genres with too few tracks")