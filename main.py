from playlist_generator import fetch_all_tracks, create_playlists_by_genre

if __name__ == "__main__":
    df = fetch_all_tracks()
    df.to_csv('output.csv', index=False)
    print("CSV file exported as output.csv")

    confirm = input("Do you want to create playlists based on this CSV? (yes/no): ")
    if confirm.lower() == 'yes':
        create_playlists_by_genre(df)
        print("Playlists created successfully.")
    else:
        print("No playlists were created.")