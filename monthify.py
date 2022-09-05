#!python3
# -*- coding: utf-8 -*-

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from track import Track
from date_parser import extract_month_and_year
from date_parser import sort_chronologically
from structlog import get_logger
from structlog.stdlib import recreate_defaults
from logging import basicConfig
from logging import DEBUG
from rich.console import Console
from datetime import datetime
from os import makedirs
from os.path import exists
from os import stat
from auth import Auth

MAX_TRIES = 3
MAX_RESULTS = 10000

recreate_defaults(log_level=None)
makedirs("logs", exist_ok=True)
basicConfig(
    filename="logs/monthly_playlist_%s.log" % (datetime.now().strftime("%d_%m_%Y")),
    encoding="utf-8",
    level=DEBUG,
)
logger = get_logger(__name__)
console = Console()
existing_playlists_file = "existing_playlists_file.dat"
last_run_file = "last_run.txt"
last_run_format = "%Y-%m-%d %H:%M:%S"


class Monthify:
    def __init__(self):
        authentication = Auth()
        self.sp = authentication.get_spotipy()
        self.current_username = self.sp.current_user()["uri"][13:]
        self.track_list = []
        self.playlist_names = []
        self.already_created_playlists_exists = False
        if exists(existing_playlists_file):
            if stat(existing_playlists_file).st_size != 0:
                with open(existing_playlists_file, "r") as f:
                    self.already_created_playlists = list(f.read().splitlines())
                    self.already_created_playlists_exists = True
            else:
                self.already_created_playlists = []
                self.already_created_playlists_exists = False
        else:
            self.already_created_playlists = []
        self.already_created_playlists_inter = []
        if exists(last_run_file):
            if stat(last_run_file).st_size != 0:
                with open(last_run_file, "r") as f:
                    self.last_run = f.read()
            else:
                self.last_run = ""
        else:
            self.last_run = ""

        self.playlist_names_with_id = []
        self.name = f"""
        ___  ___            _   _     _  __       
        |  \/  |           | | | |   (_)/ _|      
        | .  . | ___  _ __ | |_| |__  _| |_ _   _ 
        | |\/| |/ _ \| '_ \| __| '_ \| |  _| | | |
        | |  | | (_) | | | | |_| | | | | | | |_| |
        \_|  |_/\___/|_| |_|\__|_| |_|_|_|  \__, |
                                             __/ |
                                            |___/ 
        """

    def starting(self):
        """
        Staring function
        Displays project name and current username
        """
        console.print(f"""[green]%s[/green]""" % self.name)
        console.print("Username: [cyan]%s[/cyan]" % self.current_username)

    def update_last_run(self):
        """
        Updates last run time to current time
        """
        self.last_run = datetime.now().strftime(last_run_format)
        with open(last_run_file, "w") as f:
            f.write(self.last_run)

    def get_user_saved_tracks(self):
        """
        Retrieves the current user's saved spotify tracks
        """
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
        """
        Retrieves the current user's created or liked spotify playlists
        """
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
        """
        Retrieves all the tracks in a specified spotify playlist identified by playlist id
        """
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
        """
        Creates playlist with name var checking if the playlist already exists in the user's library,
        if it does the user is informed
        """
        sp = self.sp
        playlists = self.get_user_saved_playlists()
        already_created_playlists = []
        count = 0
        logger.info("Playlist creation called", name=name)
        for _, item in enumerate(playlists):
            playlist_name = str(item["name"]).encode("utf-8").lower()
            to_be_added_name = name.encode("utf-8").lower()
            # logger.info("Playlist checking", playlist_name=playlist_name, to_be_added_name=to_be_added_name)
            if playlist_name == to_be_added_name:
                count += 1
                console.print("Playlist %s already exists" % name)
                self.already_created_playlists_inter.append(name)
                logger.info("Playlist already exists", name=name)
                return
        if count != 0:
            console.print("Playlist %s already exists" % name)
        else:
            console.print("Creating playlist %s" % name)
            logger.info("Creating playlist", name=name)
            sp.user_playlist_create(
                user=self.current_username,
                name=name,
                public=False,
                collaborative=False,
                description="%s" % name,
            )
            console.print("Added %s playlist" % name)
            logger.info("Added playlist", name=name)
        self.already_created_playlists_inter = already_created_playlists

    def get_saved_track_info(self):
        """
        Collates the user's saved tracks and adds them to a list as a Track type
        """
        console.print("Retrieving user saved tracks")
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
        console.print("Finished retrieving user saved tracks")

    def get_playlist_names_names(self):
        """
        Generates month playlist names using the added_at attribute of the Track type
        """
        logger.info("Generating playlist names")
        console.print("Retrieving relevant playlist information")
        for track in self.track_list:
            month, year = track.parse_track_month()
            logger.info("Playlist name", month=month, year=year)
            self.playlist_names.append((month, year))
        unsorted_playlist_names = [*set(self.playlist_names)]
        self.playlist_names = sort_chronologically(unsorted_playlist_names)
        logger.info("Removing duplicate playlist names")
        logger.info("Final list", playlist_names=self.playlist_names)

    def get_monthly_playlist_ids(self):
        """
        Retrieves playlist ids of already created month playlists
        """
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
        console.print("Finished retrieving relevant playlist information")

    def create_monthly_playlists(self):
        """
        Creates playlists in user's library based on generated playlist names
        """
        logger.info("Creating playlists")
        last_run = ""
        if self.last_run == "":
            last_run = datetime.now().strftime(last_run_format)
        else:
            last_run = self.last_run

        if (
            datetime.strptime(last_run, last_run_format).strftime("%B")
            != datetime.now().strftime("%B")
        ) | self.already_created_playlists_exists is False:
            for month, year in self.playlist_names:
                if str(month + " '" + year[2:]) in self.already_created_playlists:
                    console.print(
                        "%s playlist already exists" % (month + " '" + year[2:])
                    )
                else:
                    name = month + " '" + year[2:]
                    self.create_playlist(name)
        else:
            console.print(
                "Playlist generation has already occurred this month, do you still want to generate "
                "playlists? (yes/no)"
            )
            if not console.input("> ").lower().startswith("y"):
                console.print("Playlist generation skipped")
            else:
                for month, year in self.playlist_names:
                    if str(month + " '" + year[2:]) in self.already_created_playlists:
                        console.print(
                            "%s playlist already exists" % (month + " '" + year[2:])
                        )
                    else:
                        name = month + " '" + year[2:]
                        self.create_playlist(name)
        if self.already_created_playlists_inter:
            self.already_created_playlists = [
                *self.already_created_playlists,
                *self.already_created_playlists_inter,
            ]
            self.already_created_playlists = list(
                dict.fromkeys(self.already_created_playlists)
            )

        if self.already_created_playlists:
            with open(existing_playlists_file, "w") as f:
                f.write("\n".join(self.already_created_playlists))

    def add_to_playlist(self, tracks_info: list, playlist_id):
        """
        Add a list of tracks to a specified playlist using playlist id
        """
        logger.info(
            "Attempting to add tracks to playlist",
            tracks=str(tracks_info),
            playlist=playlist_id,
        )
        playlist_items = self.get_playlist_items(playlist_id)
        to_be_added_uris = []
        playlist_uris = []

        for _, item in enumerate(playlist_items):
            track = item["track"]
            playlist_uris.append(track["uri"])

        for track_title, track_artist, track_uri in tracks_info:
            log = logger.bind(
                track_title=track_title,
                track_artist=track_artist,
                track_uri=track_uri,
                playlist=playlist_id,
            )
            if track_uri in playlist_uris:
                log.info("Track already in playlist")
                console.print(
                    "[bold red][-][/bold red]   [link=https://open.%s][cyan]%s by %s[/cyan][/link] already exists "
                    "in the playlist "
                    % (
                        (track_uri.replace(":", "/").replace("spotify", "spotify.com")),
                        track_title,
                        track_artist,
                    )
                )
            else:
                log.info("Track will be added to playlist")
                console.print(
                    "[bold green][+][/bold green]  [link=https://open.%s][bold green]%s by %s[/bold green][/link] "
                    "will be "
                    "added to the playlist "
                    % (
                        (track_uri.replace(":", "/").replace("spotify", "spotify.com")),
                        track_title,
                        track_artist,
                    )
                )
                to_be_added_uris.append(track_uri)
        if not to_be_added_uris:
            # logger.info("No track to add to playlist", tracks=to_be_added_uris, playlist=playlist_id)
            console.print("No tracks to add\n", style="bold red")
        else:
            # logger.info("Adding tracks to playlist", tracks=to_be_added_uris, playlist=playlist_id)
            to_be_added_uris_chunks = [
                to_be_added_uris[x : x + 100]
                for x in range(0, len(to_be_added_uris), 100)
            ]
            for chunk in to_be_added_uris_chunks:
                self.sp.playlist_add_items(playlist_id=playlist_id, items=chunk)
            console.print("\n")
        logger.info("Ended track addition")

    def sort_tracks_by_month(self):
        """
        Sorts saved tracks into appropriate monthly playlist
        """
        log = logger.bind(
            playlist_names=self.playlist_names_with_id, tracks=self.track_list
        )
        log.info("Started sort")
        console.print("Beginning playlist sort")
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
            tracks_info = []
            for track in self.track_list:
                if track.parse_track_month() == (month, year):
                    logger.info(
                        "Considered adding track to playlist",
                        title=track.title,
                        artist=track.artist,
                        uri=track.uri,
                    )
                    tracks_info.append((track.title, track.artist, track.uri))
            if not tracks_info:
                break
            else:
                logger.info(
                    "Adding tracks to playlist", tracks=tracks_info, playlist=p_id
                )
                self.add_to_playlist(tracks_info, p_id)
        console.print("Finished playlist sort")
