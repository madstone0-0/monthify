#!python3
# encoding=utf-8

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from track import Track
from date_parser import extract_month_and_year

MAX_TRIES = 3
MAX_RESULTS = 2000


class Spotify:
    def __init__(self):
        self.client_secret = "e775fe5341af41599eb2c4c639ec0702"
        self.client_id = "fa28a21045ed408bb2858a9439cd1813"
        self.redirect_uri = "http://localhost:42069"
        self.scope_read = "user-library-read"
        self.scope_read_private_playlist = "playlist-read-private"
        self.scope_modify_private_playlist = "playlist-modify-private"
        self.sp = self.spotipy_init(
            self.scope_read,
            self.scope_read_private_playlist,
            self.scope_modify_private_playlist,
        )

        self.track_list = []
        self.playlist_names = []
        self.playlist_names_with_id = []

    def spotipy_init(self, *scope):
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
            )
        )

    def get_user_saved_tracks(self):
        results = []
        tries = 0

        for i in range(0, MAX_RESULTS, 50):
            try:
                result = self.sp.current_user_saved_tracks(limit=50, offset=i)["items"]
            except ConnectionError:
                while tries <= MAX_TRIES:
                    result = self.sp.current_user_saved_tracks(limit=50, offset=i)[
                        "items"
                    ]
                    tries += 0
            if not result:
                break
            results += [*result]
        return results

    def get_user_saved_playlists(self):
        results = []
        tries = 0
        for i in range(0, MAX_RESULTS, 50):
            try:
                result = self.sp.current_user_playlists(limit=50, offset=i)["items"]
            except ConnectionError:
                while tries <= MAX_TRIES:
                    result = self.sp.current_user_playlists(limit=50, offset=i)["items"]
                    tries += 1
            if not result:
                break
            results += [*result]
        return results

    def get_playlist_items(self, playlist_id):
        results = []
        tries = 0
        for i in range(0, MAX_RESULTS, 20):
            try:
                result = self.sp.playlist_items(
                    playlist_id=playlist_id, fields=None, limit=20, offset=i
                )["items"]
            except ConnectionError:
                while tries <= MAX_TRIES:
                    result = self.sp.playlist_items(
                        playlist_id=playlist_id, fields=None, limit=20, offset=i
                    )["items"]
                    tries +=1
            if not result:
                break
            results += [*result]
        return results

    def create_playlist(self, name):
        sp = self.sp
        playlists = self.get_user_saved_playlists()
        count = 0
        for _, item in enumerate(playlists):
            playlist_name = str(item["name"]).encode("utf-8").lower()
            to_be_added_name = name.encode("utf-8").lower()
            if playlist_name == to_be_added_name:
                count += 1
                print("Playlist %s already exists" % name)
                return
        if count != 0:
            print("Playlist %s already exists" % name)
        else:
            print("Creating playlist %s" % name)
            sp.user_playlist_create(
                user="8vx0z9rwpse4fzr62po8sca1r",
                name=name,
                public=False,
                collaborative=False,
                description="%s" % name,
            )
            print("Added %s playlist" % name)

    def get_saved_track_info(self):
        tracks = self.get_user_saved_tracks()
        for _, item in enumerate(tracks):
            track = item["track"]
            self.track_list.append(
                Track(
                    track["name"],
                    track["artists"][0]["name"],
                    item["added_at"],
                    track["uri"],
                )
            )

    def get_playlist_names_names(self):
        for track in self.track_list:
            month, year = extract_month_and_year(track.added_at)
            self.playlist_names.append((month, year))
        self.playlist_names = [*set(self.playlist_names)]

    def get_monthly_playlist_ids(self):
        playlists = self.get_user_saved_playlists()
        for month, year in self.playlist_names:
            for idx, item in enumerate(playlists):
                if (month + " '" + year[2:]).encode("utf-8").lower() == item[
                    "name"
                ].encode("utf-8").lower():
                    self.playlist_names_with_id.append((month, year, item["id"]))

    def create_monthly_playlists(self):
        for month, year in self.playlist_names:
            name = month + " '" + year[2:]
            self.create_playlist(name)

    def add_to_playlist(self, track_uris: list, playlist_id):
        playlist_items = self.get_playlist_items(playlist_id)
        to_be_added_uris = []
        playlist_uris = []

        for _, item in enumerate(playlist_items):
            track = item["track"]
            playlist_uris.append(track["uri"])

        for track_uri in track_uris:
            if track_uri in playlist_uris:
                print("Track with id %s already exists in playlist" % track_uri)
            else:
                print(
                    "Track with id %s will be added to playlist with id %s"
                    % (track_uri, playlist_id)
                )
                to_be_added_uris.append(track_uri)
        if not to_be_added_uris:
            print("No tracks to add")
        else:
            self.sp.playlist_add_items(playlist_id=playlist_id, items=to_be_added_uris)

    def sort_tracks_by_month(self):
        try:
            if len(self.playlist_names) != len(self.playlist_names_with_id):
                raise Exception
        except Exception:
            raise print(
                "The playlist_names list and the playlist_names_with_id list are not the same length "
                "something has gone wrong"
            )
        for month, year, p_id in self.playlist_names_with_id:
            print("Sorting into playlist %s '%s" % (month, year[2:]))
            track_uris = []
            for track in self.track_list:
                if track.parse_track_month() == (month, year):
                    track_uris.append(track.uri)
            if not track_uris:
                break
            else:
                self.add_to_playlist(track_uris, p_id)
