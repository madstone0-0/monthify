#!python3
from auth import Spotify

if __name__ == "__main__":
    controller = Spotify()

    # Get user saved tracks
    controller.get_saved_track_info()

    # Generate names of playlists based on month and year saved tracks were added
    controller.get_playlist_names_names()

    # Create playlists based on month and year
    controller.create_monthly_playlists()

    # Retrieve playlist ids of created playlists
    controller.get_monthly_playlist_ids()

    # Add saved tracks to created playlists by month and year
    controller.sort_tracks_by_month()
