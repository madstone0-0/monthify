from pathlib import Path

from monthify.playlist import Playlist
from monthify.track import Track
from monthify.utils import sanitize_generated_playlist_name
from tests.test_data import mock_data


def test_playlist_add():
    playlist = Playlist("Test playlist")
    tracks = [
        Track(
            title=track["track"]["name"],
            artist=track["track"]["artist"],
            added_at=track["added_at"],
            uri=track["track"]["uri"],
        )
        for track in mock_data["tracks"]["items"]
    ]
    for track in tracks:
        playlist.add(track)
    assert playlist.items == tracks


def test_playlist_find():
    playlist = Playlist("Test playlist")
    tracks = [
        Track(
            title=track["track"]["name"],
            artist=track["track"]["artist"],
            added_at=track["added_at"],
            uri=track["track"]["uri"],
        )
        for track in mock_data["tracks"]["items"]
    ]
    for track in tracks:
        playlist.add(track)
    playlist.find_tracks("/home/mads/Music/Music/")
    assert len(playlist.found_items) != 0


def test_playlist_generate():
    playlist = Playlist("Test playlist")
    tracks = [
        Track(
            title=track["track"]["name"],
            artist=track["track"]["artist"],
            added_at=track["added_at"],
            uri=track["track"]["uri"],
        )
        for track in mock_data["tracks"]["items"]
    ]
    for track in tracks:
        playlist.add(track)
    playlist.find_tracks("/home/mads/Music/Music/")
    out_dir = Path("/home/mads/projects/Python/monthify/tests/test_out")
    playlist.generate_m3u(save_path=out_dir)
    file = out_dir / f"{sanitize_generated_playlist_name(playlist.name)}.m3u8"
    assert file.exists()
