from argparse import ArgumentParser, Namespace

from monthify import appname
from monthify.config import Config


def get_args(config: Config) -> ArgumentParser:
    parser = ArgumentParser(prog=appname.lower(), description="Sorts saved spotify tracks by month saved")

    creation_group = parser.add_mutually_exclusive_group()
    generate_group = parser.add_argument_group("Playlist Generation Options")

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

    parser.add_argument(
        "--profile",
        default=False,
        required=False,
        action="store_true",
        help="Profile the program for debugging purposes",
    )

    parser.add_argument(
        "--public", default=False, required=False, action="store_true", help="Set created playlists to public"
    )

    parser.add_argument(
        "--reverse", default=False, required=False, action="store_true", help="Show sort log in reverse order"
    )

    parser.add_argument(
        "--max-workers",
        metavar="max_workers",
        default=10,
        type=int,
        required=False,
        help="Max number of workers to use for  concurrent requests (default: 10, max: 20)",
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

    generate_group.add_argument(
        "--generate",
        default=False,
        required=False,
        action="store_true",
        help="Create playlists on your device based on your Spotify playlists, using songs found in your local music collection.",
    )

    generate_group.add_argument(
        "--library-path",
        metavar="library_path",
        type=str,
        help="Path to your local music library",
    )

    generate_group.add_argument(
        "--dont-use-metadata",
        default=False,
        required=False,
        action="store_true",
        help="Don't use metadata from your local music collection to generate playlists",
    )

    generate_group.add_argument(
        "--output-path",
        metavar="output_path",
        type=str,
        help="Path to save generated playlists",
    )

    generate_group.add_argument(
        "--relative",
        default=False,
        required=False,
        action="store_true",
        help="Use relative paths for playlist generation",
    )

    generate_group.add_argument(
        "--add-sorting-numbers",
        default=False,
        required=False,
        action="store_true",
        help="Add reverse incrementing numbers to the beginning of each playlist name file for alphabetical sorting",
    )

    return parser


def parse_args(parser: ArgumentParser) -> tuple[ArgumentParser, Namespace]:
    return (parser, parser.parse_args())
