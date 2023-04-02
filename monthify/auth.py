# Authentication manager
import spotipy
from spotipy.oauth2 import SpotifyOAuth

MAX_TRIES = 5


class Auth:
    def __init__(self, CLIENT_ID, CLIENT_SECRET, LOCATION):
        self.client_secret = CLIENT_SECRET
        self.client_id = CLIENT_ID
        self.redirect_uri = "https://open.spotify.com/"
        self.scopes = (
            "user-library-read",
            "playlist-read-private",
            "playlist-modify-private",
        )
        self.location = LOCATION

    def spotipy_init(self, scopes):
        return spotipy.Spotify(
            retries=MAX_TRIES,
            requests_timeout=10,
            auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=[str(scope) for scope in scopes],
                cache_path=f"{self.location}/.cache",
            ),
        )

    def get_spotipy(self) -> spotipy.Spotify:
        return self.spotipy_init(self.scopes)
