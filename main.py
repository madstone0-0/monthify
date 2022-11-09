#!python3

import argparse
import sys

from rich.console import Console

from auth import Auth
from monthify import Monthify

console = Console()
parser = argparse.ArgumentParser(
    prog="monthify", description="Sorts saved spotify tracks by month saved"
)
parser.add_argument(
    "--CLIENT_ID",
    metavar="client_id",
    type=str,
    required=True,
    help="Spotify App client id",
)

parser.add_argument(
    "--CLIENT_SECRET",
    metavar="client_secret",
    type=str,
    required=True,
    help="Spotify App client secret",
)

parser.add_argument(
    "--skip-playlist-creation",
    default=False,
    required=False,
    action="store_true",
    help="Skips playlist generation automatically if already done this month",
)

parser.add_argument(
    "--logout",
    default=False,
    required=False,
    action="store_true",
    help="Logout of currently logged in account",
)

args = parser.parse_args()
CLIENT_ID = args.CLIENT_ID
CLIENT_SECRET = args.CLIENT_SECRET
SKIP_PLAYLIST_CREATION = args.skip_playlist_creation
LOGOUT = args.logout

if not CLIENT_ID or not CLIENT_SECRET:
    console.print("Client id and secret needed to connect to spotify's servers")
    sys.exit()

if __name__ == "__main__":
    try:
        controller = Monthify(
            Auth(CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET),
            SKIP_PLAYLIST_CREATION=SKIP_PLAYLIST_CREATION,
            LOGOUT=LOGOUT,
        )

        # Logout of current account if user wishes
        controller.logout()

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
