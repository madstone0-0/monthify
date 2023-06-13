from argparse import ArgumentParser, Namespace

from monthify import appname
from monthify.config import Config


def get_args(config: Config) -> ArgumentParser:
    parser = ArgumentParser(
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

    return parser


def parse_args(parser: ArgumentParser) -> Namespace:
    return parser.parse_args()
