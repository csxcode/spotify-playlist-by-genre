from playlist_generator import fetch_all_tracks, create_playlists_by_genre
import os
import time

if __name__ == "__main__":
    print("===== Spotify Playlist by Genre =====")
    print("Starting application...")
    
    # Create output directory if it doesn't exist
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print("\nConnecting to Spotify and fetching your music data...")
    
    start_time = time.time()
    df = fetch_all_tracks()
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print(f"\nSummary of collected data:")
    print(f"- Total tracks processed: {len(df)}")
    print(f"- Unique genres found: {len(df['genre'].unique())}")
    print(f"- Time taken: {minutes} minutes {seconds} seconds")
    
    # Save to CSV
    output_path = os.path.join(output_dir, 'spotify_tracks.csv')
    print(f"\nSaving data to CSV file: {output_path}")
    df.to_csv(output_path, index=False)
    print(f"CSV file exported successfully")

    print("\n" + "=" * 40)
    confirm = input("\nDo you want to create playlists based on this CSV? (yes/no): ")
    if confirm.lower() == 'yes':
        print("\nStarting playlist creation process...")
        create_time_start = time.time()
        create_playlists_by_genre(df)
        create_time_end = time.time()
        
        create_elapsed = create_time_end - create_time_start
        create_minutes = int(create_elapsed // 60)
        create_seconds = int(create_elapsed % 60)
        
        print("\nPlaylists created successfully.")
        print(f"Time taken for playlist creation: {create_minutes} minutes {create_seconds} seconds")
    else:
        print("\nNo playlists were created.")
        
    print("\nApplication completed. Thank you for using Spotify Playlist by Genre!")