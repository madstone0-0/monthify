# Monthify
A python script that sorts liked spotify tracks into playlists by the month they were liked.
Inspired by an [IFTTT applet](https://ifttt.com/applets/rC5QtGu6-add-saved-songs-to-a-monthly-playlist) by user [t00r](https://ifttt.com/p/t00r)

## Required
- Python 3.10+
- A spotify account
- [Spotify Client_id and Client_secret](https://developer.spotify.com/documentation/general/guides/authorization/app-settings/)


## Install
```
pip install monthify
```

## Usage
```
monthify --client-id=CLIENT_ID --client-secret=CLIENT_SECRET
```

## Building
### Required
- [Poetry](https://python-poetry.org)

```
git clone https://github.com/madstone0-0/monthify.git
cd monthify
poetry install
poetry build
```