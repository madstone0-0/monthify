#! /usr/bin/python3
import argparse
import sys
from importlib.metadata import version

from appdirs import user_data_dir
from requests.exceptions import ConnectionError, ReadTimeout

from monthify import ERROR, appauthor, appname, console
from monthify.auth import Auth
from monthify.config import Config
from monthify.script import Monthify

appdata_location = user_data_dir(appname, appauthor)


config = Config()
config_args = config.get_config()

parser = argparse.ArgumentParser(
    prog=appname.lower(), description="Sorts saved spotify tracks by month saved"
)

creation_group = parser.add_mutually_exclusive_group()

parser.add_argument(
    "--CLIENT_ID",
    metavar="client_id",
    type=str,
    required=not config.is_using_config_file(),
    help="Spotify App client id",
)

parser.add_argument(
    "--CLIENT_SECRET",
    metavar="client_secret",
    type=str,
    required=not config.is_using_config_file(),
    help="Spotify App client secret",
)

parser.add_argument(
    "--logout",
    default=False,
    required=False,
    action="store_true",
    help="Logout of currently logged in account",
)

parser.add_argument(
    "--version",
    "-v",
    default=False,
    required=False,
    action="store_true",
    help="Displays version then exits",
)

creation_group.add_argument(
    "--skip-playlist-creation",
    default=False,
    required=False,
    action="store_true",
    help="Skips playlist generation automatically",
)

creation_group.add_argument(
    "--create-playlists",
    default=False,
    required=False,
    action="store_true",
    help="Forces playlist generation",
)

args = parser.parse_args()

SKIP_PLAYLIST_CREATION = args.skip_playlist_creation
CREATE_PLAYLIST = args.create_playlists
LOGOUT = args.logout
VERSION = args.version

if VERSION:
    console.print(f"v{version('monthify')}")
    sys.exit(0)


if not config.is_using_config_file():
    CLIENT_ID = args.CLIENT_ID
    CLIENT_SECRET = args.CLIENT_SECRET
else:
    if config is None or len(config_args) == 0:
        console.print("Config file empty")
        sys.exit(1)
    if not config_args["CLIENT_ID"] or not config_args["CLIENT_SECRET"]:
        console.print("Spotify keys not found in config file")
        sys.exit(1)
    CLIENT_ID = config_args["CLIENT_ID"]
    CLIENT_SECRET = config_args["CLIENT_SECRET"]


if not CLIENT_ID or not CLIENT_SECRET:
    console.print(
        "Client id and secret needed to connect to spotify's servers", style=ERROR
    )
    sys.exit(1)


def run():
    try:
        controller = Monthify(
            Auth(
                CLIENT_ID=CLIENT_ID,
                CLIENT_SECRET=CLIENT_SECRET,
                LOCATION=appdata_location,
                REDIRECT="https://open.spotify.com/",
                SCOPES=(
                    "user-library-read",
                    "playlist-read-private",
                    "playlist-modify-private",
                ),
            ),
            SKIP_PLAYLIST_CREATION=SKIP_PLAYLIST_CREATION,
            LOGOUT=LOGOUT,
            CREATE_PLAYLIST=CREATE_PLAYLIST,
        )

        # Starting info
        controller.starting()

        # Get user saved tracks
        controller.get_saved_track_info()

        # Generate names of playlists based on month and year saved tracks were added
        controller.get_playlist_names_names()

        # Create playlists based on month and year
        controller.create_monthly_playlists()

        # Retrieve playlist ids of created playlists
        controller.get_monthly_playlist_ids()

        # Add saved tracks to created playlists by month and year
        controller.sort_tracks_by_month()

        # Update last run time
        controller.update_last_run()
    except KeyboardInterrupt:
        console.print("Exiting...")
    except (ConnectionError, ReadTimeout):
        console.print(
            "Cannot connect to Spotify servers, please check your internet connection and try again",
            style=ERROR,
        )
        sys.exit(1)


if __name__ == "__main__":
    run()
