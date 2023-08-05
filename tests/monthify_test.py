from monthify.script import Monthify

class SpotifyMock:
    def __init__(self):
        self.username = "Hudson"
        self.playlists = {
            {}
        }
        self.saved_songs = {
            {}
        }


class AuthMock:
    def get_spotipy(self):
        return SpotifyMock()

