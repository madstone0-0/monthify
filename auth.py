#!python3
# -*- coding: utf-8 -*-
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Auth:
    def __init__(self, CLIENT_ID, CLIENT_SECRET):
        self.client_secret = CLIENT_SECRET
        self.client_id = CLIENT_ID
        self.redirect_uri = "https://open.spotify.com/"
        self.scope_read = "user-library-read"
        self.scope_read_private_playlist = "playlist-read-private"
        self.scope_modify_private_playlist = "playlist-modify-private"

    def spotipy_init(self, *scope):
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
            )
        )

    def get_spotipy(self) -> spotipy.Spotify:
        return self.spotipy_init(
            self.scope_read,
            self.scope_read_private_playlist,
            self.scope_modify_private_playlist,
        )

