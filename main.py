from playlist_generator import fetch_all_tracks, create_playlists_by_genre
import os

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = fetch_all_tracks()
    output_path = os.path.join(output_dir, 'spotify_tracks.csv')
    df.to_csv(output_path, index=False)
    print(f"CSV file exported as {output_path}")

    confirm = input("Do you want to create playlists based on this CSV? (yes/no): ")
    if confirm.lower() == 'yes':
        create_playlists_by_genre(df)
        print("Playlists created successfully.")
    else:
        print("No playlists were created.")