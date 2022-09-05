#!python3
# Track class to manage track data

from date_parser import extract_month_and_year


class Track:
    """
    Parses and stores data such as title and artist about tracks retrieved from the spotify api
    """
    def __init__(self, title, artist, added_at, uri):
        self.title = title
        self.artist = artist
        self.added_at = added_at
        self.uri = uri

    def parse_track_month(self) -> (str, str):
        """
        Parses the date a track was added into a tuple of strings
        """
        return extract_month_and_year(self.added_at)
