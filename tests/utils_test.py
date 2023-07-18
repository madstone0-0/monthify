import random

from pytest import mark

from monthify.utils import extract_month_and_year, normalize_text, search_normalized, sort_chronologically
from tests.test_data import date_data, playlist_data, search_data, text_data


@mark.parametrize(
    "date, expected",
    [date for date in date_data],
)
def test_extract_month_and_year(date, expected):
    got = extract_month_and_year(date)
    assert got == expected


@mark.parametrize(
    "playlists, expected",
    [
        *[playlist for playlist in playlist_data],
        (reversed(playlist_data[0][0]), playlist_data[0][1]),
        (
            [
                random.sample(playlist_data[0][0], len(playlist_data[0][0])),
                playlist_data[0][1],
            ]
        ),
        (reversed(playlist_data[1][0]), playlist_data[1][1]),
        (
            [
                random.sample(playlist_data[1][0], len(playlist_data[1][0])),
                playlist_data[1][1],
            ]
        ),
    ],
)
def test_sort_chronologically(playlists, expected):
    got = sort_chronologically(playlists)
    assert got == expected


@mark.parametrize("text, expected", [text for text in text_data])
def test_normalize_text(text, expected):
    got = normalize_text(text)
    assert got == expected


@mark.parametrize("dataset, target, expected", [test for test in search_data])
def test_search_normalized(dataset, target, expected):
    got = search_normalized(dataset, target)
    assert got == expected
