# Script
import sys
from datetime import datetime
from os import makedirs, remove, stat
from os.path import exists
from pathlib import Path

from cachetools import cached, TTLCache
from loguru import logger
from rich.console import Console

from track import Track
from utils import (
    sort_chronologically,
    normalize_text,
    conditional_decorator,
)

MAX_RESULTS = 10000

makedirs("logs", exist_ok=True)
logger.add(
    sys.stderr,
    format="{time} {level} {message}",
    filter="monthify",
    level="INFO",
)
logger.remove()
logger.add("logs/monthify.log", rotation="00:00", compression="zip")
console = Console()
existing_playlists_file = "existing_playlists_file.dat"
last_run_file = "last_run.txt"
last_run_format = "%Y-%m-%d %H:%M:%S"
saved_tracks_cache = TTLCache(maxsize=1000, ttl=86400)
saved_playlists_cache = TTLCache(maxsize=1000, ttl=86400)
user_cache = TTLCache(maxsize=1, ttl=86400)


class Monthify:
    def __init__(self, auth, SKIP_PLAYLIST_CREATION, LOGOUT, CREATE_PLAYLIST):
        authentication = auth
        self.sp = authentication.get_spotipy()
        self.SKIP_PLAYLIST_CREATION = SKIP_PLAYLIST_CREATION
        self.CREATE_PLAYLIST = CREATE_PLAYLIST
        self.LOGOUT = LOGOUT
        self.has_created_playlists = False
        self.current_username = self.get_username()["uri"][13:]
        self.current_display_name = self.get_username()["display_name"]
        self.track_list = []
        self.playlist_names = []
        self.already_created_playlists_exists = False
        if (
            exists(existing_playlists_file)
            and stat(existing_playlists_file).st_size != 0
        ):
            if (
                datetime.now()
                - datetime.fromtimestamp(
                    Path(existing_playlists_file).stat().st_ctime
                )
            ).days >= 30:
                remove(existing_playlists_file)
                self.already_created_playlists = []
                self.already_created_playlists_exists = False
            else:
                with open(existing_playlists_file, "r", encoding="utf_8") as f:
                    self.already_created_playlists = list(f.read().splitlines())
                    self.already_created_playlists_exists = True
        else:
            self.already_created_playlists = []
            self.already_created_playlists_exists = False

        self.already_created_playlists_inter = []
        if exists(last_run_file):
            if stat(last_run_file).st_size != 0:
                with open(last_run_file, "r", encoding="utf_8") as f:
                    self.last_run = f.read()
            else:
                self.last_run = ""
        else:
            self.last_run = ""

        self.playlist_names_with_id = []
        self.name = f"""
        [green]
        ___  ___            _   _     _  __       
        |  \/  |           | | | |   (_)/ _|      
        | .  . | ___  _ __ | |_| |__  _| |_ _   _ 
        | |\/| |/ _ \| '_ \| __| '_ \| |  _| | | |
        | |  | | (_) | | | | |_| | | | | | | |_| |
        \_|  |_/\___/|_| |_|\__|_| |_|_|_|  \__, |
                                             __/ |
                                            |___/ 
        written by [link=https://github.com/madstone0-0]madstone0-0[/link]
        [/green]
        """

    def logout(self):
        if self.LOGOUT is True:
            try:
                remove("./.cache")
                logger.info("Successfully deleted .cache file, user logged out")
            except FileNotFoundError:
                console.print("Not logged into any account", style="bold red")
                logger.error("Cache file doesn't exist")

    def starting(self):
        """
        Staring function
        Displays project name and current username
        """
        logger.info("Starting script execution")
        console.print(self.name)
        console.print(f"Username: [cyan]{self.current_display_name}[/cyan]")

    def update_last_run(self):
        """
        Updates last run time to current time
        """
        self.last_run = datetime.now().strftime(last_run_format)
        with open(last_run_file, "w", encoding="utf_8") as f:
            f.write(self.last_run)

    @cached(user_cache)
    def get_username(self):
        return self.sp.current_user()

    @cached(saved_tracks_cache)
    def get_user_saved_tracks(self):
        """
        Retrieves the current user's saved spotify tracks
        """
        logger.info("Starting user saved tracks fetch")
        results = []
        result = self.sp.current_user_saved_tracks(limit=50)
        while result:
            results += [*result["items"]]
            if result["next"]:
                result = self.sp.next(result)
            else:
                result = None
        logger.info("Ending user saved tracks fetch")
        return results

    @conditional_decorator(
        cached(saved_playlists_cache), "has_created_playlists"
    )
    def get_user_saved_playlists(self):
        """
        Retrieves the current user's created or liked spotify playlists
        """
        logger.info("Starting user saved playlists fetch")
        results = []
        result = self.sp.current_user_playlists(limit=50)
        while result:
            results += [*result["items"]]
            if result["next"]:
                result = self.sp.next(result)
            else:
                result = None
        logger.info("Ending user saved playlists fetch")
        return results

    def get_playlist_items(self, playlist_id):
        """
        Retrieves all the tracks in a specified spotify playlist identified by playlist id
        """
        logger.info(
            f"Starting playlist item fetch\n id: {playlist_id}", playlist_id
        )
        results = []
        result = self.sp.playlist_items(
            playlist_id=playlist_id, fields=None, limit=20
        )
        while result:
            results += [*result["items"]]
            if result["next"]:
                result = self.sp.next(result)
            else:
                result = None
        logger.info(f"Ending playlist item fetch\n id: {playlist_id}")
        return results

    def create_playlist(self, name):
        """
        Creates playlist with name var checking if the playlist already exists in the user's library,
        if it does the user is informed
        """
        sp = self.sp
        playlists = self.get_user_saved_playlists()
        already_created_playlists = []
        created_playlists = []
        count = 0
        logger.info(f"Playlist creation called {name}")
        for _, item in enumerate(playlists):
            if normalize_text(item["name"]) == normalize_text(name):
                count += 1
                console.print(f"Playlist {name} already exists")
                self.already_created_playlists_inter.append(name)
                logger.info(f"Playlist already exists {name}")
                return
        if count != 0:
            console.print(f"Playlist {name} already exists")
        else:
            console.print(f"Creating playlist {name}")
            logger.info(f"Creating playlist {name}")
            playlist = sp.user_playlist_create(
                user=self.current_username,
                name=name,
                public=False,
                collaborative=False,
                description=f"{name}",
            )
            created_playlists.append(playlist)
            console.print(f"Added {name} playlist")
            logger.info(f"Added {name} playlist")
        self.has_created_playlists = (
            True if created_playlists.__len__() > 0 else False
        )
        self.already_created_playlists_inter = already_created_playlists

    def get_saved_track_info(self):
        """
        Collates the user's saved tracks and adds them to a list as a Track type
        """
        with console.status("Retrieving user saved tracks"):
            tracks = self.get_user_saved_tracks()
            logger.info("Retrieving saved track info")
            self.track_list = [
                Track(
                    title=item["track"]["name"],
                    artist=item["track"]["artists"][0]["name"],
                    added_at=item["added_at"],
                    uri=item["track"]["uri"],
                )
                for _, item in enumerate(tracks)
            ]

    def get_playlist_names_names(self):
        """
        Generates month playlist names using the added_at attribute of the Track type
        """
        logger.info("Generating playlist names")
        self.playlist_names = [track.track_month for track in self.track_list]
        unsorted_playlist_names = [*set(self.playlist_names)]
        self.playlist_names = sort_chronologically(unsorted_playlist_names)
        logger.info("Removing duplicate playlist names")
        logger.info(f"Final list: {self.playlist_names}")

    def get_monthly_playlist_ids(self):
        """
        Retrieves playlist ids of already created month playlists
        """
        logger.info("Retrieving playlist ids")
        with console.status("Retrieving relevant playlist information"):
            playlists = self.get_user_saved_playlists()
            for month, year in self.playlist_names:
                for idx, item in enumerate(playlists):
                    if normalize_text(
                        (month + " '" + year[2:])
                    ) == normalize_text(item["name"]):
                        self.playlist_names_with_id.append(
                            (month, year, item["id"])
                        )
                        logger.info(
                            "Playlist name: {name} id: {id}",
                            name=str(month + " '" + year[2:]),
                            id=str(item["id"]),
                        )

    def create_monthly_playlists(self):
        """
        Creates playlists in user's library based on generated playlist names
        """
        logger.info("Creating playlists")
        spotify_playlists = [
            item[1]["name"]
            for item in enumerate(self.get_user_saved_playlists())
        ]
        monthly_ran = False
        if self.last_run == "":
            last_run = datetime.now().strftime(last_run_format)
        else:
            last_run = self.last_run

        def playlist_loop():
            for month, year in self.playlist_names:
                playlist_name = str(month + " '" + year[2:])
                if (
                    playlist_name in self.already_created_playlists
                    and playlist_name in spotify_playlists
                ):
                    console.print(
                        f"{month} '{year[2:]} playlist already exists"
                    )
                else:
                    name = month + " '" + year[2:]
                    self.create_playlist(name)

        def skip(status: bool):
            if status is True:
                console.print("Playlist generation skipped")
                logger.info("Playlist generation skipped")
            else:
                logger.info("Playlist generation starting")
                playlist_loop()

        if (
            datetime.strptime(last_run, last_run_format).strftime("%B")
            != datetime.now().strftime("%B")
        ) and self.already_created_playlists_exists is False:
            monthly_ran = True
            playlist_loop()

        if self.CREATE_PLAYLIST is False:
            if (
                self.SKIP_PLAYLIST_CREATION is False
                and monthly_ran is False
                or self.already_created_playlists_exists is False
            ):
                console.print(
                    "Playlist generation has already occurred this month, do you still want to generate "
                    "playlists? (yes/no)"
                )
                logger.info("Requesting playlist creation")

                if not console.input("> ").lower().startswith("y"):
                    skip(True)
                else:
                    skip(False)
            else:
                skip(True)
        else:
            skip(False)

        if self.already_created_playlists_inter:
            self.already_created_playlists = [
                *self.already_created_playlists,
                *self.already_created_playlists_inter,
            ]
            self.already_created_playlists = list(
                dict.fromkeys(self.already_created_playlists)
            )

        if self.already_created_playlists:
            with open(existing_playlists_file, "w", encoding="utf_8") as f:
                f.write("\n".join(self.already_created_playlists))

    def add_to_playlist(self, tracks: list[Track], playlist_id):
        """
        Add a list of tracks to a specified playlist using playlist id
        """
        logger.info(
            "Attempting to add tracks to playlist: {playlist}\ntracks: {tracks} ",
            tracks=tracks,
            playlist=str(playlist_id),
        )
        playlist_items = self.get_playlist_items(playlist_id)
        to_be_added_uris, playlist_uris = [], []

        playlist_uris = [
            item["track"]["uri"] for _, item in enumerate(playlist_items)
        ]

        for track in tracks:
            if track.uri in playlist_uris:
                logger.info(
                    f"Track: {track} already in playlist: {str(playlist_id)}"
                )
                track_url = f'https://open.{track.uri.replace(":", "/").replace("spotify", "spotify.com")}'
                console.print(
                    f"[bold red][-][/bold red]\t[link={track_url}][cyan]{track.title} by {track.artist}[/cyan][/link] already exists "
                    "in the playlist "
                )
            else:
                logger.info(
                    f"Track: {track} will be added to playlist: {str(playlist_id)}"
                )
                track_url = f'https://open.{track.uri.replace(":", "/").replace("spotify", "spotify.com")}'
                console.print(
                    f"[bold green][+][/bold green]\t[link={track_url}][bold green]{track.title} by {track.artist}[/bold green][/link] "
                    "will be "
                    "added to the playlist "
                )
                to_be_added_uris.append(track.uri)
        if not to_be_added_uris:
            logger.info(
                "No tracks to add to playlist: {playlist}", playlist=playlist_id
            )
            console.print("\t\n")
        else:
            logger.info(
                "Adding tracks: {tracks} to playlist: {playlist}",
                tracks=(" ".join(to_be_added_uris)),
                playlist=playlist_id,
            )
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
            playlist_names=self.playlist_names_with_id,
            tracks=[track.title for track in self.track_list],
        )
        log.info("Started sort")
        console.print("Beginning playlist sort")
        try:
            if len(self.playlist_names) != len(self.playlist_names_with_id):
                raise Exception
        except RuntimeError as error:
            log.error(
                "playlist_names and playlist_names_with_id are not the same length",
                playlist_names_length=self.playlist_names.__len__(),
                playlist_names_with_id_length=self.playlist_names_with_id.__len__(),
                error=error,
            )
            raise print(
                "The playlist_names list and the playlist_names_with_id list are not the same length "
                f"something has gone wrong error={error}"
            )

        with console.status("Sorting Tracks"):
            for month, year, playlist_id in self.playlist_names_with_id:
                logger.info(
                    "Sorting into playlist: {playlist}",
                    playlist=(month, year[2:]),
                )
                playlist_url = (
                    f"https://open.spotify.com/playlist/{playlist_id}"
                )
                playlist_name = f"{month} '{year[2:]}"

                console.rule(
                    f"Sorting into playlist [link={playlist_url}]{playlist_name}[/link]"
                )
                console.print("\t\n")
                tracks = [
                    track
                    for track in self.track_list
                    if track.track_month == (month, year)
                ]
                if not tracks:
                    break
                else:
                    logger.info(
                        "Adding tracks to playlist: {playlist}",
                        playlist=str(playlist_id),
                    )
                    self.add_to_playlist(tracks, playlist_id)

        console.print("Finished playlist sort")
        logger.info("Finished script execution")
