from monthify.track import Track
from monthify.utils import extract_month_and_year


def test_track_init():
    # test track initialization
    added_at = "2019-11-09T22:20:28Z"
    title = "Basket Case"
    artist = "Green Day"
    uri = "spotify:track:6L89mwZXSOwYl76YXfX13s"
    track = Track(title=title, artist=artist, added_at=added_at, uri=uri)

    assert track.title == title
    assert track.artist == artist
    assert track.added_at == added_at
    assert track.uri == uri
    assert track.track_month == extract_month_and_year(added_at)
