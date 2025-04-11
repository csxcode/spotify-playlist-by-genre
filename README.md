# Spotify Playlist by Genre

Python script to extract all your songs from Spotify (Liked Songs + Playlists), classify them by genre, export to CSV, and optionally create private playlists based on genres.

## Setup

1. Create Spotify App: https://developer.spotify.com/dashboard
2. Get client_id, client_secret, redirect_uri
3. Get the username from the Spotify profile page
4. Create `.env` file, then copy entries from `.env.example` file and set the valid values

### Setting up Virtual Environment (Mac)

1. Open Terminal
2. Navigate to the project directory:
```bash
cd path/to/spotify-playlist-by-genre
```

3. Create a virtual environment:
```bash
python3 -m venv env
```

4. Activate the virtual environment:
```bash
source env/bin/activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

6. Run the script:
```bash
python main.py
```

7. When finished, you can deactivate the virtual environment:
```bash
deactivate
```

## Notes
- The script will create playlists with the prefix "[Auto]" to identify automatically generated playlists
- Genres with fewer than 3 songs will be excluded from playlist creation (this will be displayed in the console)
