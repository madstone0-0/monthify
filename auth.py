#!python3
# encoding=utf-8

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from track import Track
from date_parser import extract_month_and_year
import structlog
import logging
from rich.console import Console
from datetime import datetime

MAX_TRIES = 3
MAX_RESULTS = 10000

structlog.stdlib.recreate_defaults(log_level=None)
logging.basicConfig(
    filename="monthly_playlist_%s.log" % (datetime.now().strftime("%d_%m_%Y_%H_%M_%S")), encoding="utf-8", level=logging.INFO
)
logger = structlog.get_logger(__name__)
console = Console()


class Spotify:
    def __init__(self):
        self.client_secret = "e775fe5341af41599eb2c4c639ec0702"
        self.client_id = "fa28a21045ed408bb2858a9439cd1813"
        self.redirect_uri = "http:/localhost/"
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
        logger.info("Starting user saved tracks fetch")
        for i in range(0, MAX_RESULTS, 50):
            try:
                result = self.sp.current_user_saved_tracks(limit=50, offset=i)["items"]
            except ConnectionError:
                logger.error(
                    "Failed to reach spotify server trying", max_retries=MAX_TRIES
                )
                while tries <= MAX_TRIES:
                    logger.info("Retrying...", attempt=tries)
                    result = self.sp.current_user_saved_tracks(limit=50, offset=i)[
                        "items"
                    ]
                    tries += 0
            if not result:
                break
            results += [*result]
        logger.info("Ending user saved tracks fetch")
        return results

    def get_user_saved_playlists(self):
        results = []
        tries = 0
        logger.info("Starting user saved playlists fetch")
        for i in range(0, MAX_RESULTS, 50):
            try:
                result = self.sp.current_user_playlists(limit=50, offset=i)["items"]
            except ConnectionError:
                logger.error(
                    "Failed to reach spotify server trying", max_retries=MAX_TRIES
                )
                while tries <= MAX_TRIES:
                    logger.info("Retrying...", attempt=tries)
                    result = self.sp.current_user_playlists(limit=50, offset=i)["items"]
                    tries += 1
            if not result:
                break
            results += [*result]
        logger.info("Ending user saved playlists fetch")
        return results

    def get_playlist_items(self, playlist_id):
        results = []
        tries = 0
        logger.info("Starting playlist item fetch", playlist_id=playlist_id)
        for i in range(0, MAX_RESULTS, 20):
            try:
                result = self.sp.playlist_items(
                    playlist_id=playlist_id, fields=None, limit=20, offset=i
                )["items"]
            except ConnectionError:
                logger.error(
                    "Failed to reach spotify server trying", max_retries=MAX_TRIES
                )
                while tries <= MAX_TRIES:
                    logger.info("Retrying...", attempt=tries)
                    result = self.sp.playlist_items(
                        playlist_id=playlist_id, fields=None, limit=20, offset=i
                    )["items"]
                    tries += 1
            if not result:
                break
            results += [*result]
        logger.info("Ending playlist item fetch", playlist_id=playlist_id)
        return results

    def create_playlist(self, name):
        sp = self.sp
        playlists = self.get_user_saved_playlists()
        count = 0
        logger.info("Playlist creation called", name=name)
        for _, item in enumerate(playlists):
            playlist_name = str(item["name"]).encode("utf-8").lower()
            to_be_added_name = name.encode("utf-8").lower()
            # logger.info("Playlist checking", playlist_name=playlist_name, to_be_added_name=to_be_added_name)
            if playlist_name == to_be_added_name:
                count += 1
                console.print("Playlist %s already exists" % name)
                logger.info("Playlist already exists", name=name)
                return
        if count != 0:
            console.print("Playlist %s already exists" % name)
        else:
            console.print("Creating playlist %s" % name)
            logger.info("Creating playlist", name=name)
            sp.user_playlist_create(
                user="8vx0z9rwpse4fzr62po8sca1r",
                name=name,
                public=False,
                collaborative=False,
                description="%s" % name,
            )
            console.print("Added %s playlist" % name)
            logger.info("Added playlist", name=name)

    def get_saved_track_info(self):
        tracks = self.get_user_saved_tracks()
        logger.info("Retrieving saved track info")
        # logger.info("Saved tracks", tracks=tracks)
        for _, item in enumerate(tracks):
            track = item["track"]
            # logger.info("Assigning values to new Track type instance")
            logger.info(
                "Track type",
                title=track["name"],
                artist=track["artists"][0]["name"],
                added_at=item["added_at"],
                uri=track["uri"],
            )
            self.track_list.append(
                Track(
                    track["name"],
                    track["artists"][0]["name"],
                    item["added_at"],
                    track["uri"],
                )
            )

    def get_playlist_names_names(self):
        logger.info("Generating playlist names")
        for track in self.track_list:
            month, year = extract_month_and_year(track.added_at)
            logger.info("Playlist name", month=month, year=year)
            self.playlist_names.append((month, year))
        unsorted_playlist_names = [*set(self.playlist_names)]
        self.playlist_names = sorted(
            unsorted_playlist_names,
            key=lambda d: (d[1], datetime.strptime(d[0], "%B")),
            reverse=True,
        )
        logger.info("Removing duplicate playlist names")
        logger.info("Final list", playlist_names=self.playlist_names)

    def get_monthly_playlist_ids(self):
        logger.info("Retrieving playlist ids")
        playlists = self.get_user_saved_playlists()
        for month, year in self.playlist_names:
            for idx, item in enumerate(playlists):
                if (month + " '" + year[2:]).encode("utf-8").lower() == item[
                    "name"
                ].encode("utf-8").lower():
                    self.playlist_names_with_id.append((month, year, item["id"]))
                    logger.info(
                        "Playlist name with ids",
                        name=(month + " '" + year[2:]),
                        id=item["id"],
                    )

    def create_monthly_playlists(self):
        logger.info("Creating playlists")
        for month, year in self.playlist_names:
            name = month + " '" + year[2:]
            self.create_playlist(name)
            # logger.info("Created playlist", name=name)

    def add_to_playlist(self, track_uris: list, playlist_id):
        logger.info(
            "Attempting to add tracks to playlist",
            tracks=str(track_uris),
            playlist=playlist_id,
        )
        playlist_items = self.get_playlist_items(playlist_id)
        to_be_added_uris = []
        playlist_uris = []

        for _, item in enumerate(playlist_items):
            track = item["track"]
            playlist_uris.append(track["uri"])

        for track_uri in track_uris:
            log = logger.bind(track=track_uri, playlist=playlist_id)
            if track_uri in playlist_uris:
                log.info("Track already in playlist")
                console.print(
                    "Track [bold green]https://open.%s[/bold green] already exists in the playlist"
                    % (track_uri.replace(":", "/").replace("spotify", "spotify.com"))
                )
            else:
                log.info("Track will be added to playlist")
                console.print(
                    "Track with id [bold green]https://open.%s[/bold green] will be added to the playlist"
                    % (track_uri.replace(":", "/").replace("spotify", "spotify.com"))
                )
                to_be_added_uris.append(track_uri)
        if not to_be_added_uris:
            # logger.info("No track to add to playlist", tracks=to_be_added_uris, playlist=playlist_id)
            console.print("No tracks to add", style="bold red")
        else:
            # logger.info("Adding tracks to playlist", tracks=to_be_added_uris, playlist=playlist_id)
            self.sp.playlist_add_items(playlist_id=playlist_id, items=to_be_added_uris)
        logger.info("Ended track addition")

    def sort_tracks_by_month(self):
        log = logger.bind(
            playlist_names=self.playlist_names_with_id, tracks=self.track_list
        )
        log.info("Started sort")
        try:
            if len(self.playlist_names) != len(self.playlist_names_with_id):
                raise Exception
        except Exception:
            log.error(
                "playlist_names and playlist_names_with_id are not the same length",
                playlist_names_length=self.playlist_names.__len__(),
                playlist_names_with_id_length=self.playlist_names_with_id.__len__(),
            )
            raise print(
                "The playlist_names list and the playlist_names_with_id list are not the same length "
                "something has gone wrong"
            )
        for month, year, p_id in self.playlist_names_with_id:
            logger.info("Sorting into playlist", playlist=(month, year[2:]))
            console.print(
                "Sorting into playlist %s '%s https://open.spotify.com/playlist/%s"
                % (month, year[2:], p_id)
            )
            console.rule()
            track_uris = []
            for track in self.track_list:
                if track.parse_track_month() == (month, year):
                    logger.info(
                        "Considered adding track to playlist",
                        title=track.title,
                        artist=track.artist,
                        uri=track.uri,
                    )
                    track_uris.append(track.uri)
            if not track_uris:
                break
            else:
                logger.info(
                    "Adding tracks to playlist", tracks=track_uris, playlist=p_id
                )
                self.add_to_playlist(track_uris, p_id)
