#! /usr/bin/python3
import argparse
import sys
from importlib.metadata import version

import toml
from appdirs import user_config_dir, user_data_dir
from requests.exceptions import ConnectionError, ReadTimeout
from rich.console import Console

from monthify import ERROR
from monthify.auth import Auth
from monthify.script import Monthify

CONFIG_FILE_NAME = "monthify.toml"
using_config_file = False
appname = "Monthify"
appauthor = "madstone0-0"
appdata_location = user_data_dir(appname, appauthor)

console = Console()
parser = argparse.ArgumentParser(
    prog="monthify", description="Sorts saved spotify tracks by month saved"
)

if sys.platform == "win32" or sys.platform == "darwin":
    appconfig_location = appdata_location
else:
    appconfig_location = user_config_dir(appname.lower(), appauthor)


config = None
try:
    with open(
        f"{appconfig_location}/{CONFIG_FILE_NAME}", "r", encoding="utf-8"
    ) as config_file:
        using_config_file = True
        config = toml.load(config_file)
except FileNotFoundError:
    using_config_file = False
except toml.TomlDecodeError:
    console.print("Invalid config document", style=ERROR)
    sys.exit(1)


creation_group = parser.add_mutually_exclusive_group()

parser.add_argument(
    "--CLIENT_ID",
    metavar="client_id",
    type=str,
    required=not using_config_file,
    help="Spotify App client id",
)

parser.add_argument(
    "--CLIENT_SECRET",
    metavar="client_secret",
    type=str,
    required=not using_config_file,
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
if not using_config_file:
    CLIENT_ID = args.CLIENT_ID
    CLIENT_SECRET = args.CLIENT_SECRET
else:
    if config is None or len(config) == 0:
        console.print("Config file empty")
        sys.exit(1)
    if not config["CLIENT_ID"] or not config["CLIENT_SECRET"]:
        console.print("Spotify keys not found in config file")
        sys.exit(1)
    CLIENT_ID = config["CLIENT_ID"]
    CLIENT_SECRET = config["CLIENT_SECRET"]


SKIP_PLAYLIST_CREATION = args.skip_playlist_creation
CREATE_PLAYLIST = args.create_playlists
LOGOUT = args.logout
VERSION = args.version

if not CLIENT_ID or not CLIENT_SECRET:
    console.print(
        "Client id and secret needed to connect to spotify's servers", style=ERROR
    )
    sys.exit(1)


def run():
    if VERSION:
        console.print(f"v{version('monthify')}")
        sys.exit(0)

    try:
        controller = Monthify(
            Auth(
                CLIENT_ID=CLIENT_ID,
                CLIENT_SECRET=CLIENT_SECRET,
                LOCATION=appdata_location,
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
