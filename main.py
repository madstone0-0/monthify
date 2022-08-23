#!python3
from auth import Spotify

if __name__ == "__main__":
    controller = Spotify()
    controller.get_saved_track_info()
    controller.print_saved_track_info()
    # controller.get_playlist_names_names()