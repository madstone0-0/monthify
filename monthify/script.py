# Script
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from os import remove, stat
from os.path import exists
from pathlib import Path
from time import perf_counter
from typing import Iterable, Iterator, List, Optional, Reversible, Tuple

from cachetools import TTLCache, cached

from monthify import ERROR, SUCCESS, appdata_location, console, logger
from monthify.auth import Auth
from monthify.track import Track
from monthify.utils import conditional_decorator, normalize_text, sort_chronologically

MAX_RESULTS = 10000
CACHE_LIFETIME = 30
MAX_WORKERS = 10

existing_playlists_file = f"{appdata_location}/existing_playlists_file.dat"
last_run_file = f"{appdata_location}/last_run.txt"
last_run_format = "%Y-%m-%d %H:%M:%S"
saved_tracks_cache: TTLCache = TTLCache(maxsize=1000, ttl=86400)
saved_playlists_cache: TTLCache = TTLCache(maxsize=1000, ttl=86400)
user_cache: TTLCache = TTLCache(maxsize=1, ttl=86400)
playlist_items_cache: TTLCache = TTLCache(maxsize=100, ttl=86400)


class Monthify:
    def __init__(
        self, auth: Auth, SKIP_PLAYLIST_CREATION: bool, LOGOUT: bool, CREATE_PLAYLIST: bool, MAKE_PUBLIC: bool
    ):
        self.MAKE_PUBLIC = MAKE_PUBLIC
        self.LOGOUT = LOGOUT
        self.logout()
        authentication = auth
        self.sp = authentication.get_spotipy()
        self.SKIP_PLAYLIST_CREATION = SKIP_PLAYLIST_CREATION
        self.CREATE_PLAYLIST = CREATE_PLAYLIST
        self.has_created_playlists = False
        self.current_username: str
        self.current_display_name: str
        self.playlist_names: List[Tuple[str, str]]
        self.total_tracks_added = 0
        self.already_created_playlists_exists = False
        if exists(existing_playlists_file) and stat(existing_playlists_file).st_size != 0:
            if (
                datetime.now() - datetime.fromtimestamp(Path(existing_playlists_file).stat().st_ctime)
            ).days >= CACHE_LIFETIME:
                remove(existing_playlists_file)
                self.already_created_playlists = set([])
                self.already_created_playlists_exists = False
            else:
                with open(existing_playlists_file, "r", encoding="utf_8") as f:
                    self.already_created_playlists = set(f.read().splitlines())
                    self.already_created_playlists_exists = True
        else:
            self.already_created_playlists = set([])
            self.already_created_playlists_exists = False

        if exists(last_run_file) and stat(last_run_file).st_size != 0:
            with open(last_run_file, "r", encoding="utf_8") as f:
                self.last_run = f.read()
        else:
            self.last_run = ""

        self.playlist_names_with_id: List[Tuple[str, str, str]] = []
        self.name = r"""
        ___  ___            _   _     _  __       
        |  \/  |           | | | |   (_)/ _|      
        | .  . | ___  _ __ | |_| |__  _| |_ _   _ 
        | |\/| |/ _ \| '_ \| __| '_ \| |  _| | | |
        | |  | | (_) | | | | |_| | | | | | | |_| |
        \_|  |_/\___/|_| |_|\__|_| |_|_|_|  \__, |
                                             __/ |
                                            |___/ 
        written by [link=https://github.com/madstone0-0]madstone0-0[/link]
        """

    def logout(self) -> None:
        if self.LOGOUT is True:
            try:
                remove(f"{appdata_location}/.cache")
                console.print("Successfully logged out of saved account", style=SUCCESS)
                logger.info("Successfully deleted .cache file, user logged out")
                sys.exit(0)
            except FileNotFoundError:
                console.print("Not logged into any account", style=ERROR)
                logger.error("Cache file doesn't exist")
                sys.exit(0)

    def starting(self) -> None:
        """
        Staring function
        Displays project name and current username
        """

        logger.info("Starting script execution")
        console.print(self.name, style="green")
        with console.status("Retrieving user information"):
            self.current_display_name = self.get_username()["display_name"]
            self.current_username = self.get_username()["id"]
        console.print(f"Username: [cyan]{self.current_display_name}[/cyan]\n")

    def update_last_run(self) -> None:
        """
        Updates last run time to current time
        """

        self.last_run = datetime.now().strftime(last_run_format)
        with open(last_run_file, "w", encoding="utf_8") as f:
            f.write(self.last_run)

    def get_results(self, result):
        """
        Retrieves all results from a spotify api call
        """

        results = []
        while result:
            results += [*result["items"]]
            if result["next"]:
                result = self.sp.next(result)
            else:
                result = None
        return results

    @cached(user_cache)
    def get_username(self) -> dict:
        """
        Retrieves the current user's spotify information
        """

        return self.sp.current_user()

    @cached(saved_tracks_cache)
    def get_user_saved_tracks(self) -> List[dict]:
        """
        Retrieves the current user's saved spotify tracks
        """

        logger.info("Starting user saved tracks fetch")
        results = self.get_results(self.sp.current_user_saved_tracks(limit=50))
        logger.info("Ending user saved tracks fetch")
        return results

    @conditional_decorator(cached(saved_playlists_cache), "has_created_playlists")
    def get_user_saved_playlists(self):
        """
        Retrieves the current user's created or liked spotify playlists
        """

        logger.info("Starting user saved playlists fetch")
        results = self.get_results(self.sp.current_user_playlists(limit=50))
        logger.info("Ending user saved playlists fetch")
        return results

    @cached(playlist_items_cache)
    def get_playlist_items(self, playlist_id: str) -> List[dict]:
        """
        Retrieves all the tracks in a specified spotify playlist identified by playlist id
        """

        logger.info(f"Starting playlist item fetch\n id: {playlist_id}", playlist_id)
        results = self.get_results(self.sp.playlist_items(playlist_id=playlist_id, fields=None, limit=20))
        logger.info(f"Ending playlist item fetch\n id: {playlist_id}")
        return results

    def create_playlist(self, name: str) -> str:
        """
        Creates playlist with name var checking if the playlist already exists in the user's library,
        if it does the user is informed
        """

        sp = self.sp
        playlists = self.get_user_saved_playlists()
        created_playlists = []
        logger.info(f"Playlist creation called {name}")
        t0 = perf_counter()
        log = ""

        for item in playlists:
            if normalize_text(item["name"]) == normalize_text(name):
                log += f"Playlist {name} already exists"
                self.already_created_playlists.add(name)
                logger.info(f"Playlist already exists {name}")
                logger.debug(f"Playlist creation took {perf_counter() - t0} s")
                return log

        logger.debug(f"Playlist creation took {perf_counter() - t0} s")
        log += "\n" f"Creating playlist {name}"
        logger.info(f"Creating playlist {name}")
        playlist = sp.user_playlist_create(
            user=self.current_username, name=name, public=self.MAKE_PUBLIC, collaborative=False, description=f"{name}"
        )
        created_playlists.append(playlist)
        log += "\n" f"Added {name} playlist"
        log += "\n"
        logger.info(f"Added {name} playlist")
        self.has_created_playlists = len(created_playlists) > 0
        return log

    def get_saved_track_info(self) -> None:
        """
        Calls the get_saved_track_gen function at program's start to cache the user's saved tracks
        """

        with console.status("Retrieving user saved tracks"):
            self.get_saved_track_gen()

    def get_saved_track_gen(self) -> Iterator[Track]:
        """
        Collates the user's saved tracks and adds them to a list as a Track type
        """

        tracks = self.get_user_saved_tracks()
        logger.info("Retrieving saved track info")
        return (
            Track(
                title=item["track"]["name"],
                artist=item["track"]["artists"][0]["name"],
                added_at=item["added_at"],
                uri=item["track"]["uri"],
            )
            for item in tracks
        )

    def get_playlist_names_names(self):
        """
        Generates month playlist names using the added_at attribute of the Track type
        """

        logger.info("Generating playlist names")
        self.playlist_names = tuple(track.track_month for track in self.get_saved_track_gen())
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
                for item in playlists:
                    if normalize_text((month + " '" + year[2:])) == normalize_text(item["name"]):
                        self.playlist_names_with_id.append((month, year, item["id"]))
                        logger.info(
                            "Playlist name: {name} id: {id}", name=str(month + " '" + year[2:]), id=str(item["id"])
                        )

    def skip(self, status: bool, playlists: Optional[Iterable] = None) -> None:
        """
        Skips playlist generation if status is True
        """

        if status is True:
            console.print("Playlist generation skipped")
            logger.info("Playlist generation skipped")
        else:
            logger.info("Playlist generation starting")
            if playlists is None:
                RuntimeError("Playlists have not passed been passed to skip function")
            t0 = perf_counter()
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                playlist_names = [str(month + " '" + year[2:]) for month, year in self.playlist_names]

                logs = executor.map(self.create_playlist, playlist_names)
                for log in logs:
                    if log is not None:
                        console.print(log)

            logger.debug(f"Entire playlist generation took {perf_counter() - t0} s")

    def create_monthly_playlists(self):
        """
        Creates playlists in user's library based on generated playlist names
        """

        logger.info("Creating playlists")
        with console.status("Generating playlists"):
            spotify_playlists = [item["name"] for item in self.get_user_saved_playlists()]

        monthly_ran = False
        last_run = datetime.now().strftime(last_run_format) if not self.last_run else self.last_run

        has_month_passed = datetime.strptime(last_run, last_run_format).strftime("%B") != datetime.now().strftime("%B")
        if has_month_passed and self.already_created_playlists_exists is False:
            self.skip(False, spotify_playlists)
        elif not has_month_passed and self.already_created_playlists_exists:
            monthly_ran = True

        if self.CREATE_PLAYLIST is False:
            if self.SKIP_PLAYLIST_CREATION is False and monthly_ran is False:
                console.print("Playlist generation has not occurred this month, Generating Playlists...")
                logger.info("Requesting playlist creation")
                self.skip(False, spotify_playlists)

            elif self.SKIP_PLAYLIST_CREATION is False and monthly_ran is True:
                console.print(
                    "Playlist generation has already occurred this month, do you still want to generate "
                    "playlists? (yes/no)"
                )
                logger.info("Requesting playlist creation")

                if not console.input("> ").lower().startswith("y"):
                    self.skip(True)
                else:
                    self.skip(False, spotify_playlists)

            elif not self.already_created_playlists_exists:
                console.print("Somehow the playlists do not exist. Generating Playlists...")
                logger.info("Requesting playlist creation")
                self.skip(False, spotify_playlists)

            else:
                self.skip(True)

        else:
            self.skip(False, spotify_playlists)

        if self.already_created_playlists:
            with open(existing_playlists_file, "w", encoding="utf_8") as f:
                f.write("\n".join(self.already_created_playlists))

    def add_to_playlist(self, tracks: Reversible[Track], playlist_id: str) -> str:
        """
        Add a list of tracks to a specified playlist using playlist id
        """

        logger.info(
            "Attempting to add tracks to playlist: {playlist}\ntracks: {tracks} ",
            tracks=tracks,
            playlist=str(playlist_id),
        )
        playlist_items = self.get_playlist_items(playlist_id)
        to_be_added_uris: List[str] = []

        playlist_uris: Iterable[str] = tuple(item["track"]["uri"] for item in playlist_items)
        log: str = ""

        for track in reversed(tracks):
            if track.uri in playlist_uris:
                logger.info(f"Track: {track} already in playlist: {str(playlist_id)}")
                track_url = f'https://open.{track.uri.replace(":", "/").replace("spotify", "spotify.com")}'
                log += (
                    "\n"
                    f"[bold red][-][/bold red]\t[link={track_url}][cyan]{track.title} by {track.artist}[/cyan][/link]"
                    " already exists in the playlist"
                )
            else:
                logger.info(f"Track: {track} will be added to playlist: {str(playlist_id)}")
                track_url = f'https://open.{track.uri.replace(":", "/").replace("spotify", "spotify.com")}'
                log += (
                    "\n"
                    f"[bold green][+][/bold green]\t[link={track_url}][bold green]{track.title} by {track.artist}"
                    "[/bold green][/link]"
                    " will be added to the playlist "
                )
                to_be_added_uris.append(track.uri)
        log += "\n"

        if not to_be_added_uris:
            logger.info("No tracks to add to playlist: {playlist}", playlist=playlist_id)
            log += "\t\n"
        else:
            logger.info(
                "Adding tracks: {tracks} to playlist: {playlist}",
                tracks=(" ".join(to_be_added_uris)),
                playlist=playlist_id,
            )
            to_be_added_uris_chunks = tuple(to_be_added_uris[x : x + 100] for x in range(0, len(to_be_added_uris), 100))
            for chunk in to_be_added_uris_chunks:
                self.sp.playlist_add_items(playlist_id=playlist_id, items=chunk)
            log += "\n"
            self.total_tracks_added += len(to_be_added_uris)

        logger.info("Ended track addition")
        return log

    def sort_tracks_by_month(self, playlist: Tuple[str, str, str]) -> List[str]:
        month, year, playlist_id = playlist
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        playlist_name = f"{month} '{year[2:]}"
        logger.info("Sorting into playlist: {playlist}", playlist=playlist_name)
        log: list[str] = []

        tracks = tuple(track for track in self.get_saved_track_gen() if track.track_month == (month, year))
        if not tracks:
            return log
        else:
            log.append(f"Sorting into playlist [link={playlist_url}]{playlist_name}[/link]")
            log.append("\t\n")

            logger.info("Adding tracks to playlist: {playlist}", playlist=str(playlist_id))
            t0 = perf_counter()
            addedLog = self.add_to_playlist(tracks, playlist_id)
            logger.debug(f"Finished adding tracks to playlist: {str(playlist_id)} in {perf_counter() - t0:.2f}s")
            log.append(addedLog)
            return log

    def sort_all_tracks_by_month(self):
        """
        Sorts saved tracks into appropriate monthly playlist
        """

        log = logger.bind(
            playlist_names=self.playlist_names_with_id, tracks=[track.title for track in self.get_saved_track_gen()]
        )

        log.info("Started sort")

        console.print("\nBeginning playlist sort")
        try:
            if len(self.playlist_names) != len(self.playlist_names_with_id):
                raise RuntimeError("playlist_names and playlist_names_with_id are not the same length")
        except RuntimeError as error:
            log.error(
                "playlist_names and playlist_names_with_id are not the same length",
                playlist_names_length=self.playlist_names.__len__(),
                playlist_names_with_id_length=self.playlist_names_with_id.__len__(),
                error=error,
            )
            console.print(
                f"Something has gone wrong error='{error}',"
                " please run the program again with the --create-playlists flag",
                style=ERROR,
            )
            sys.exit(1)

        t0 = perf_counter()
        with console.status("Sorting Tracks"):
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                logs = executor.map(self.sort_tracks_by_month, self.playlist_names_with_id)
                for log in logs:
                    console.rule(log[0])
                    console.print("".join(log[1:]), end="")

        logger.debug(f"Finished sorting tracks in {perf_counter() - t0:.2f}s")

        count = ""
        if self.total_tracks_added == 0:
            count = "No new tracks added"
        elif self.total_tracks_added == 1:
            count = "One track added"
        elif self.total_tracks_added > 1:
            count = f"Total tracks added to playlists: {self.total_tracks_added}"

        console.print(count)
        console.print("Finished playlist sort")
        logger.info("Finished script execution")

    def clean_playlist(self, playlist_id: str):
        counts = dict()
        tracks_to_remove = []
        items = self.get_playlist_items(playlist_id)
        snapshot_id = self.sp.playlist(playlist_id, fields="snapshot_id")["snapshot_id"]
        for idx, item in enumerate(items):
            counts[item["track"]["uri"]] = {
                "count": (counts.get(item["track"]["uri"], {"count": 0, "positions": []}))["count"] + 1,
                "positions": [idx + 1],
            }

        for item_id, values in counts.items():
            if values["count"] > 1:
                tracks_to_remove.append({"uri": item_id.split(":")[2], "positions": values["positions"]})

        if tracks_to_remove:
            tracks_to_remove_chunks = (tracks_to_remove[x : x + 100] for x in range(0, len(tracks_to_remove), 100))
            for chunk in tracks_to_remove_chunks:
                self.sp.playlist_remove_specific_occurrences_of_items(
                    playlist_id=playlist_id, items=chunk, snapshot_id=snapshot_id
                )
