#!python3
# encoding=utf-8

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import datetime
import logging

logging.basicConfig(level=logging.DEBUG, filename="auth.log", filemode="w", format='%(asctime)s - %(name)s - %(message)s')
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s")


def extract_month_and_year(date) -> (str, str):
    datem = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    year = datem.year
    month = datem.strftime("%B")
    return str(month), str(year)


class Spotify:

    def __init__(self):
        self.client_secret = "e775fe5341af41599eb2c4c639ec0702"
        self.client_id = "fa28a21045ed408bb2858a9439cd1813"
        self.redirect_uri = "http://localhost:42069"
        self.scope_read = "user-library-read"
        self.scope_read_private_playlist = "playlist-read-private"
        self.scope_modify_private_playlist = "playlist-modify-private"
        self.sp = self.spotipy_init(self.scope_read, self.scope_read_private_playlist, self.scope_modify_private_playlist)

        self.track_list = []
        self.playlist_names = []

    def spotipy_init(self, *scope):
        return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.client_id, client_secret=self.client_secret, redirect_uri=self.redirect_uri, scope=scope))

    def get_user_saved_tracks(self):
        results = []
        logging.info("Starting saved tracks fetch")
        for i in range(0, 1000, 50):
            result = self.sp.current_user_saved_tracks(limit=50, offset=i)["items"]
            logging.debug("Fetching iteration %s of 1000" % i)
            if not result:
                break
            results += [*result]
        logging.info("Ended saved tracks fetch")
        return results

    def list_user_saved_tracks(self):
        results = self.get_user_saved_tracks()
        for idx, item in enumerate(results):
            track = item["track"]
            # print(track)
            print(f"{idx:5} | {item['added_at']} |{track['artists'][0]['name']:15} - {track['name']}")

    def get_user_saved_playlists(self):
        sp = self.sp
        results = []
        logging.info("Starting saved playlists fetch")
        for i in range(0, 1000, 50):
            result = sp.current_user_playlists(limit=50, offset=i)["items"]
            logging.debug("Fetching iteration %s of 1000" % i)
            if not result:
                break
            results += [*result]
        logging.info("Ended saved playlists fetch")
        return results

    def list_user_saved_playlists(self):
        results = self.get_user_saved_playlists()
        for idx, item in enumerate(results):
            print(f"{idx:5} | {item['name'].encode('utf-8')} | {item['id']}")

    def create_playlist(self, name):
        sp = self.sp
        playlists = self.get_user_saved_playlists()
        logging.info("Starting playlist creation")
        count = 0
        for _, item in enumerate(playlists):
            playlist_name = str(item["name"]).encode("utf-8").lower()
            to_be_added_name = name.encode("utf-8").lower()
            if playlist_name == to_be_added_name:
                count += 1
                print("Playlist %s already exists" % name)
                logging.info("Playlist %s already exists" % name)
                return
        if count != 0:
            print("Playlist %s already exists" % name)
            logging.info("Playlist %s already exists" % name)
        else:
            sp.user_playlist_create(user="8vx0z9rwpse4fzr62po8sca1r", name=name, public=False, collaborative=False, description="%s playlist" % name)
            print("Added %s playlist" % name)
            logging.info("Added %s playlist" % name)

    def get_saved_track_info(self):
        logging.info("Starting saved track info fetch")
        tracks = self.get_user_saved_tracks()
        for _, item in enumerate(tracks):
            track = item["track"]
            self.track_list.append(list((track["name"], track["artists"][0]["name"], item["added_at"], track["uri"])))
        logging.info("Ended saved track info fetch")

    def print_saved_track_info(self):
        print(f"{'Title':30} | {'Artist':30} | {'Added_At':30} | {'URI':30}")
        for title, artist, added_at, uri in self.track_list:
            print(f"{title:30} | {artist:30} | {added_at:>30} | {uri:>30}")

    def get_playlist_names_names(self):
        for _, _, date, _ in self.track_list:
            month, year = extract_month_and_year(date)
            self.playlist_names.append((month, year))
        self.playlist_names = [*set(self.playlist_names)]

    def create_monthly_playlists(self):
        logging.info("Starting monthly playlist creation")
        for month, year in self.playlist_names:
            name = month + " '" + year[2:]
            self.create_playlist(name)
        logging.info("Ended monthly playlist creation")
