import pandas as pd
from spotify_client import get_spotify_client
import time
import json
import os

sp = get_spotify_client()

# Cache for storing artist genres
artist_genre_cache = {}
CACHE_FILE = 'output/artist_genre_cache.json'
# Genre mapping from the fallback file
genre_mapping = {}
GENRE_MAPPING_FILE = 'data/playlist_genre_fallback.json'
# Artist genre fallback mapping
artist_genre_fallback = {}
ARTIST_GENRE_FALLBACK_FILE = 'data/artists_genre_fallback.json'

def normalize_string(text):
    """Normalize a string for consistent comparison (lowercase, trim spaces)"""
    if not text:
        return text
    return ' '.join(text.lower().split())

def load_artist_genre_fallback():
    """Load the artist-genre fallback data from file"""
    global artist_genre_fallback
    if os.path.exists(ARTIST_GENRE_FALLBACK_FILE):
        try:
            with open(ARTIST_GENRE_FALLBACK_FILE, 'r') as f:
                artist_data = json.load(f)
                
            # Create a mapping from artist name to genre
            for item in artist_data:
                normalized_artist = normalize_string(item['artist'])
                artist_genre_fallback[normalized_artist] = item['genre']
                    
            print(f"Loaded artist-genre fallback data for {len(artist_genre_fallback)} artists")
        except Exception as e:
            print(f"Error loading artist-genre fallback: {e}")
            artist_genre_fallback = {}
    else:
        print(f"Artist-genre fallback file not found at {ARTIST_GENRE_FALLBACK_FILE}")
        artist_genre_fallback = {}

def load_genre_mapping():
    """Load the genre mapping from the fallback file"""
    global genre_mapping
    if os.path.exists(GENRE_MAPPING_FILE):
        try:
            with open(GENRE_MAPPING_FILE, 'r') as f:
                genre_groups = json.load(f)
                
            # Create a mapping from each alias to the main genre
            for group in genre_groups:
                # Standardize the main genre format (first letter of each word uppercase)
                main_genre = group['genre']
                main_genre = ' '.join(word.capitalize() for word in main_genre.split())
                
                # Add the main genre itself as an alias
                genre_mapping[normalize_string(main_genre)] = main_genre
                
                for alias in group['aliases']:
                    genre_mapping[normalize_string(alias)] = main_genre
                    
            print(f"Loaded genre mappings for {len(genre_groups)} genre groups")
        except Exception as e:
            print(f"Error loading genre mapping: {e}")
            genre_mapping = {}
    else:
        print(f"Genre mapping file not found at {GENRE_MAPPING_FILE}")
        genre_mapping = {}

def map_genre(original_genre):
    """Map a genre to a more general category if it exists in the mapping"""
    if not original_genre or original_genre == 'Unknown':
        return original_genre
        
    # Check if this genre has a mapping
    normalized_genre = normalize_string(original_genre)
    if normalized_genre in genre_mapping:
        mapped_genre = genre_mapping[normalized_genre]
        return mapped_genre
    
    # If no mapping found, standardize the format for consistency
    return ' '.join(word.capitalize() for word in original_genre.split())

def load_cache():
    """Load the artist genre cache from disk if it exists"""
    global artist_genre_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                artist_genre_cache = json.load(f)
            print(f"Loaded {len(artist_genre_cache)} cached artist genres")
        except Exception as e:
            print(f"Error loading cache: {e}")
            artist_genre_cache = {}
    else:
        artist_genre_cache = {}

def save_cache():
    """Save the artist genre cache to disk"""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(artist_genre_cache, f)
        print(f"Saved {len(artist_genre_cache)} artist genres to cache")
    except Exception as e:
        print(f"Error saving cache: {e}")

def fetch_all_tracks():
    # Load existing cache at the start
    load_cache()
    # Load genre mapping
    load_genre_mapping()
    # Load artist-genre fallback data
    load_artist_genre_fallback()
    
    print("Starting to fetch all tracks...")
    results = []
    track_count = 0
    artist_ids_to_fetch = set()  # Set to avoid duplicates
    track_artist_mapping = {}  # Mapping of tracks to their artists

    # User's saved tracks
    print("Fetching your saved/liked tracks...")
    saved_tracks = sp.current_user_saved_tracks(limit=50)
    saved_count = 0
    while saved_tracks:
        for item in saved_tracks['items']:
            track = item['track']
            artist_id = track['artists'][0]['id']
            artist_name = track['artists'][0]['name']
            
            # Store track and artist information for later processing
            track_data = {
                'song': track['name'],
                'artist': artist_name,
                'genre': None,  # Will be filled later
                'url': track['external_urls']['spotify']
            }
            results.append(track_data)
            
            # Add artist to the list to query if not in cache
            if artist_id not in artist_genre_cache:
                artist_ids_to_fetch.add(artist_id)
                track_artist_mapping[track['id']] = {'artist_id': artist_id, 'track_data': track_data}
            else:
                # If we already have the genre in cache, assign it directly with mapping
                original_genre = artist_genre_cache[artist_id]
                mapped_genre = map_genre(original_genre)
                track_data['genre'] = mapped_genre or 'Unknown'
            
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
    excluded_playlists = 0
    current_user_id = sp.me()['id']
    
    for playlist in playlists['items']:
        # Check if the current user is the owner of the playlist
        if playlist['owner']['id'] != current_user_id:
            print(f"Excluding playlist: {playlist['name']} (not created by you)")
            excluded_playlists += 1
            continue
            
        playlist_count += 1
        print(f"\nProcessing playlist {playlist_count}/{len(playlists['items']) - excluded_playlists}: {playlist['name']}")
        tracks = sp.playlist_tracks(playlist['id'], limit=100)
        playlist_track_count = 0
        while tracks:
            for item in tracks['items']:
                track = item['track']
                if track:
                    artist_id = track['artists'][0]['id']
                    artist_name = track['artists'][0]['name']
                    
                    # Store track and artist information for later processing
                    track_data = {
                        'song': track['name'],
                        'artist': artist_name,
                        'genre': None,  # Will be filled later
                        'url': track['external_urls']['spotify']
                    }
                    results.append(track_data)
                    
                    # Add artist to the list to query if not in cache
                    if artist_id not in artist_genre_cache:
                        artist_ids_to_fetch.add(artist_id)
                        track_artist_mapping[track['id']] = {'artist_id': artist_id, 'track_data': track_data}
                    else:
                        # If we already have the genre in cache, assign it directly with mapping
                        original_genre = artist_genre_cache[artist_id]
                        mapped_genre = map_genre(original_genre)
                        track_data['genre'] = mapped_genre or 'Unknown'
                    
                    playlist_track_count += 1
                    track_count += 1
                    
            if tracks['next']:
                print(f"Processed {playlist_track_count} tracks in this playlist so far, fetching more...")
                tracks = sp.next(tracks)
            else:
                break
        print(f"Completed processing {playlist_track_count} tracks from playlist: {playlist['name']}")
    
    # Fetch artist genres in batches
    fetch_artist_genres_in_batches(list(artist_ids_to_fetch), track_artist_mapping)
    
    # Apply artist genre fallback for tracks with Unknown genre
    apply_artist_genre_fallback(results, track_artist_mapping)
    
    print(f"\nFinished processing a total of {len(results)} tracks.")
    print(f"Excluded {excluded_playlists} playlists that were not created by you.")
    return pd.DataFrame(results)

def fetch_artist_genres_in_batches(artist_ids, track_artist_mapping):
    """Obtain artist genres in batches of 50 (maximum allowed by Spotify API)"""
    if not artist_ids:
        return
        
    print(f"\nFetching genres for {len(artist_ids)} unique artists...")
    batches = [artist_ids[i:i+50] for i in range(0, len(artist_ids), 50)]
    
    for i, batch in enumerate(batches):
        print(f"Fetching batch {i+1}/{len(batches)} of artists...")
        artists = sp.artists(batch)['artists']
        
        for artist in artists:
            # Save original genre to cache
            original_genre = artist['genres'][0] if artist['genres'] else None
            artist_genre_cache[artist['id']] = original_genre
            
            # Map the genre if needed
            mapped_genre = map_genre(original_genre)
            
            # Update all tracks associated with this artist
            for track_id, info in track_artist_mapping.items():
                if info['artist_id'] == artist['id']:
                    info['track_data']['genre'] = mapped_genre if mapped_genre else 'Unknown'
        
        # Respect API rate limits
        if i < len(batches) - 1:
            time.sleep(0.5)
    
    # Save the updated cache to disk
    save_cache()

def fetch_artist_genre(artist_id):
    """Function maintained for compatibility, now uses cache"""
    if artist_id in artist_genre_cache:
        original_genre = artist_genre_cache[artist_id]
        return map_genre(original_genre)
    
    artist = sp.artist(artist_id)
    original_genre = artist['genres'][0] if artist['genres'] else None
    artist_genre_cache[artist_id] = original_genre
    return map_genre(original_genre)

def count_potential_playlists(df, min_tracks=3):
    """Count how many playlists could be created based on genre distribution
    
    Returns:
        tuple: (count of potential playlists, dict of genre names with their track counts)
    """
    potential_playlists = 0
    potential_genres = {}
    genres_count = df['genre'].value_counts()
    
    for genre, count in genres_count.items():
        if count >= min_tracks:
            potential_playlists += 1
            potential_genres[genre] = count
            
    return potential_playlists, potential_genres

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
            
        print(f"Creating playlist: {playlist_prefix} {genre}")
        playlist = sp.user_playlist_create(user=sp.me()['id'], name=f"{playlist_prefix} {genre}", public=False)
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

def apply_artist_genre_fallback(tracks, track_artist_mapping):
    """Apply the artist genre fallback for tracks with Unknown genre"""
    unknown_count = 0
    fallback_applied = 0
    cache_updated = False
    
    for track in tracks:
        if track['genre'] is None or track['genre'] == 'Unknown':
            unknown_count += 1
            normalized_artist = normalize_string(track['artist'])
            if normalized_artist in artist_genre_fallback:
                # Get genre from fallback and apply mapping if needed
                original_genre = artist_genre_fallback[normalized_artist]
                mapped_genre = map_genre(original_genre)
                track['genre'] = mapped_genre
                fallback_applied += 1
                
                # Find tracks with this artist that have artist IDs in the mapping
                for track_id, info in track_artist_mapping.items():
                    if normalize_string(info['track_data']['artist']) == normalized_artist:
                        # Update cache with the fallback genre for this artist ID
                        artist_id = info['artist_id']
                        if artist_id not in artist_genre_cache or artist_genre_cache[artist_id] is None:
                            artist_genre_cache[artist_id] = original_genre
                            cache_updated = True
                
    print(f"\nFound {unknown_count} tracks with unknown genre")
    print(f"Applied artist genre fallback to {fallback_applied} tracks")
    
    # Save the updated cache if changes were made
    if cache_updated:
        save_cache()
        print(f"Updated artist genre cache with fallback data")