import pytest

from monthify.script import Monthify
from tests.test_data import mock_data


class SpotifyMock:
    def __init__(self):
        self.username = mock_data["username"]
        self.playlists = mock_data["playlists"]
        self.saved_tracks = mock_data["tracks"]

    def current_user_playlists(self, limit=50, offset=0):
        return self.playlists

    def current_user(self):
        return self.username

    def current_user_saved_tracks(self, limit=50, offset=0):
        return self.saved_tracks


class AuthMock:
    def get_spotipy(self):
        return SpotifyMock()


@pytest.fixture
def monthify():
    return Monthify(AuthMock(), True, False, False, False)


def test_get_display_name(monthify):
    username = monthify.get_username()
    display_name = username["display_name"]
    assert display_name == "Hudson"


def test_get_user_id(monthify):
    id = monthify.get_username()["id"]
    assert id == "8vx0z9rwpse4fzr62po8sca1r"


def test_get_user_playlists(monthify):
    playlists = monthify.get_user_saved_playlists()
    assert playlists == mock_data["playlists"]["items"]


def test_get_user_tracks(monthify):
    tracks = monthify.get_user_saved_tracks()
    assert tracks == mock_data["tracks"]["items"]
