import sqlite3 as sql
from pathlib import Path
from traceback import format_exc
from typing import Iterable, Optional, cast

from loguru import logger
from mutagen import File
from mutagen.easyid3 import EasyID3
from pathvalidate import sanitize_filename as sani

from monthify import appdata_location
from monthify.track import Track
from monthify.utils import horspool, sanitize_filename, sanitize_generated_playlist_name, track_binary_search

FILE_EXTS = {".mp3", ".flac", ".wav", ".m4a"}
DB_PATH = Path(appdata_location) / "libraryCache.db"
SCHEMA = """drop table if exists file_cache;
drop table if exists metadata_cache;

create table if not exists file_cache(name character varying, path character varying);
create table if not exists metadata_cache(name character varying, path character varying, title character varying, artist character varying);"""


def clear_cache():
    with sql.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for line in SCHEMA.splitlines():
            cursor.execute(line)
        conn.commit()


class Playlist:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.items: list[Track] = []
        self.found_items: list[str] = []

    def fill(self, items: Iterable[Track]) -> None:
        self.items = list(items)

    def add(self, item: Track) -> None:
        self.items.append(item)

    def _parse_file_metadata(self, file: Path) -> Optional[dict[str, str]]:
        metadata = File(file)
        resDict: dict[str, str] = {}

        try:
            resDict["title"] = metadata["title"][0]
            resDict["artist"] = metadata["artist"][0]
        except KeyError:
            logger.info(f"Cannot find metadata on track {file.stem} trying id3")
            try:
                id3Data = EasyID3(file)
                resDict["title"] = id3Data["title"][0]
                resDict["artist"] = id3Data["artist"][0]
            except Exception:
                logger.info(f"Cannot find id3 data skipping track: {file.stem}")
                return None
        return resDict

    def create_cache_db(self) -> None:
        with sql.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for line in SCHEMA.splitlines():
                cursor.execute(line)
            conn.commit()

    def write_to_file_cache_db(self, data: tuple[tuple[str, Path], ...]) -> None:
        with sql.connect(DB_PATH) as conn:
            storeData = ((name, str(path)) for name, path in data)
            conn.executemany("insert into file_cache values (?, ?)", storeData)

            conn.commit()

    def write_to_metadata_cache_db(self, data: tuple[tuple[str, Path, dict[str, str] | None], ...]) -> None:
        with sql.connect(DB_PATH) as conn:
            storeData = []
            for name, path, metadata in data:
                if metadata:
                    storeData.append((name, str(path), metadata["title"], metadata["artist"]))
                else:
                    storeData.append((name, str(path), "", ""))

            conn.executemany("insert into metadata_cache values (?, ?, ?, ?)", storeData)

            conn.commit()

    def read_from_file_cache_db(self) -> tuple[tuple[str, Path], ...]:
        with sql.connect(DB_PATH) as conn:
            data = cast(tuple[tuple[str, Path], ...], conn.execute("select * from file_cache").fetchall())
            data = tuple((name, Path(path)) for name, path in data)
        return data

    def read_from_metadata_cache_db(self) -> tuple[tuple[str, Path, dict[str, str]], ...]:
        with sql.connect(DB_PATH) as conn:
            data = cast(
                tuple[tuple[str, Path, dict[str, str]], ...], conn.execute("select * from metadata_cache").fetchall()
            )
            data = tuple((name, Path(path), {"title": title, "artist": artist}) for name, path, title, artist in data)
        return data

    def is_file_cache_valid(self) -> bool:
        with sql.connect(DB_PATH) as conn:
            try:
                data = conn.execute("select * from file_cache").fetchall()
                if len(data) == 0:
                    return False
            except sql.OperationalError:
                return False
        return True

    def is_metadata_cache_valid(self) -> bool:
        with sql.connect(DB_PATH) as conn:
            try:
                data = conn.execute("select * from metadata_cache").fetchall()
                if len(data) == 0:
                    return False
            except sql.OperationalError:
                return False
        return True

    def find_tracks(self, search_path: Path, use_metadata: bool = True) -> list[Track]:
        if isinstance(search_path, str):
            search_path = Path(search_path)

        if self.is_file_cache_valid():
            logger.info("Using cache")
            files = self.read_from_file_cache_db()
        else:
            logger.info("Cache invalid, searching for files")
            files = tuple(
                sorted(
                    (
                        (sanitize_filename(file.stem), file)
                        for file in search_path.rglob("*", recurse_symlinks=True)
                        if file.suffix in FILE_EXTS
                    ),
                    key=lambda x: x[0],
                )
            )
            self.write_to_file_cache_db(files)

        logger.info(f"Found {len(files)} files")
        searchTerms = self.items[:]

        if use_metadata:
            if self.is_metadata_cache_valid():
                logger.info("Using metadata cache")
                filesWithMetadata = self.read_from_metadata_cache_db()
            else:
                logger.info("Metadata cache invalid, processing metadata")
                filesWithMetadata = tuple(map(lambda x: (x[0], x[1], self._parse_file_metadata(x[1])), files))
                self.write_to_metadata_cache_db(filesWithMetadata)

            filteredFilesWMetadata: tuple[tuple[str, Path, dict[str, str]], ...] = tuple(
                filter(lambda x: x[2] is not None, filesWithMetadata)
            )

            for item in reversed(searchTerms):
                artistTracks = filter(
                    lambda x: horspool(item.artist.lower(), x[2]["artist"].lower()), filteredFilesWMetadata
                )
                searchFiles = tuple(map(lambda x: (x[0], x[1]), artistTracks))
                idx = track_binary_search(sani(item.title), searchFiles)
                if idx is None:
                    continue
                file = searchFiles[idx]
                self.found_items.append(str(file[1]))
                searchTerms.remove(item)
        else:
            for item in reversed(searchTerms):
                idx = track_binary_search(sani(item.title), files)

                if not idx:
                    continue
                file = files[idx]
                self.found_items.append(str(file[1]))
                searchTerms.remove(item)

        logger.info(f"Finished file search found {len(self.found_items)} out of {len(self.items)} tracks")
        return searchTerms

    def generate_m3u(self, save_path: Path, relative: bool = False, root_path: Optional[Path] = None) -> None:
        if isinstance(save_path, str):
            save_path = Path(save_path)

        if len(self.found_items) == 0:
            raise RuntimeError("Cannot generate M3U with no files")
        if relative and root_path is None:
            raise RuntimeError("If relative is set to true a root_path must be suppiled")
        root_path = cast(Path, root_path)

        try:
            with open(
                save_path / f"{sanitize_generated_playlist_name(self.name)}.m3u8", mode="+w", encoding="utf-8"
            ) as f:
                f.write("#EXTM3U\n")
                f.write(f"#PLAYLIST:{self.name}\n")
                for item in self.found_items:
                    if relative:
                        relpath = Path(item).relative_to(root_path)
                        f.write(f"../{relpath}\n")
                    else:
                        f.write(item + "\n")
        except Exception as e:
            tb = format_exc()
            logger.error(f"Error generating playlist {self.name}: {e}")
            logger.error(f"Traceback:\n{tb}")
