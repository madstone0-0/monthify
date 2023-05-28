# Authentication manager
from collections.abc import Iterable

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Auth:
    def __init__(
        self,
        CLIENT_ID: str,
        CLIENT_SECRET: str,
        LOCATION: str,
        SCOPES: Iterable[str],
        REDIRECT: str,
        MAX_TRIES: int = 5,
        TIMEOUT: int = 10,
    ):
        self.client_secret = CLIENT_SECRET
        self.client_id = CLIENT_ID
        self.redirect_uri = REDIRECT
        self.scopes = SCOPES
        self.location = LOCATION
        self.retries = MAX_TRIES
        self.timeout = TIMEOUT

    def get_spotipy(self) -> spotipy.Spotify:
        return spotipy.Spotify(
            retries=self.retries,
            requests_timeout=self.timeout,
            auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                # scope=[str(scope) for scope in scopes],
                scope=self.scopes,
                cache_path=f"{self.location}/.cache",
            ),
        )
