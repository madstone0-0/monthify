import os
import sqlite3 as sql
from collections import defaultdict
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from pathlib import Path
from traceback import format_exc
from typing import Dict, Iterable, List, Optional, Set, cast

from loguru import logger
from mutagen import File
from mutagen.easyid3 import EasyID3
from pathvalidate import sanitize_filename as sf

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
    files: Optional[tuple[tuple[str, Path], ...]] = None
    metadata: Optional[tuple[tuple[str, Path, dict[str, str]], ...]] = None

    def __init__(self, name: str, MAX_WORKERS: int) -> None:
        self.name: str = name
        self.items: list[Track] = []
        self.found_items: list[str] = []
        self.MAX_WORKERS = MAX_WORKERS
        self.MAX_CPU = min(cast(int, os.cpu_count()) - 1 or 1, 4)

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

    def rglob_recurse_symlinks(self, path: Path, exts: Optional[Set[str]] = None) -> List[Path]:
        paths: List[Path] = []
        visited: Set[Path] = set()
        self._rglob_recurse_symlinks_helper(path, visited, paths, exts)
        return paths

    def _rglob_recurse_symlinks_helper(
        self, path: Path, visited: Set[Path], paths: List[Path], exts: Optional[Set[str]]
    ) -> None:
        # Check if path exists before processing
        if not path.exists():
            return

        resolved = path.resolve()
        if resolved in visited:
            return
        visited.add(resolved)

        # Add the current path to the results
        if exts:
            if path.suffix in exts:
                paths.append(path)
        else:
            paths.append(path)

        # Process directory contents
        if path.is_dir():
            try:
                for item in path.iterdir():
                    self._rglob_recurse_symlinks_helper(item, visited, paths, exts)
            except PermissionError:
                pass

    def _find_track_files(self, search_path: Path) -> tuple[tuple[str, Path], ...]:
        top = []
        try:
            for i in os.scandir(search_path):
                if i.is_dir():
                    top.append(Path(i.path))
        except (PermissionError, OSError) as e:
            logger.error(f"Error accessing search path: {search_path}: {e}")
        top.append(search_path)

        temp_files: List[Path] = []
        with ProcessPoolExecutor(self.MAX_CPU) as exec:
            todo: Dict[Future[List[Path]], str] = {
                exec.submit(self.rglob_recurse_symlinks, dir, FILE_EXTS): str(dir) for dir in top
            }

            # Collect all items
            for job in as_completed(todo):
                dir = todo[job]
                try:
                    found = job.result()
                    temp_files.extend(found)
                    logger.info(f"Processed directory {dir}: {len(found)}")
                except Exception as e:
                    logger.error(f"Error processing directory {dir}: {e}")

            files = tuple(
                sorted(
                    ((sanitize_filename(file.stem), file) for file in temp_files),
                    key=lambda x: x[0],
                )
            )

            return files

    def _process_metadata(self, files: tuple[tuple[str, Path], ...]) -> tuple[tuple[str, Path, dict[str, str]], ...]:
        if self.is_metadata_cache_valid():
            if Playlist.metadata is not None:
                logger.info("Using static variable metadata")
            else:
                logger.info("Using metadata cache")
                meta = self.read_from_metadata_cache_db()
                Playlist.metadata = meta
            return Playlist.metadata

        logger.info("Metadata cache invalid, processing metadata")
        temp: List[tuple[str, Path, dict[str, str]]] = []
        with ProcessPoolExecutor(self.MAX_CPU) as exec:
            todo = {exec.submit(self._parse_file_metadata, path): (name, path) for name, path in files}

            for job in as_completed(todo):
                name, path = todo[job]
                try:
                    metadata = job.result()
                    temp.append((name, path, cast(dict[str, str], metadata)))
                    logger.info(f"Processed metadata for {path}")
                except Exception:
                    logger.error(f"Failed to parse metadata for {path}")

        filesWithMetadata = tuple(temp)
        self.write_to_metadata_cache_db(filesWithMetadata)

        return filesWithMetadata

    def _search_with_metadata(
        self, filesWithMetadata: tuple[tuple[str, Path, dict[str, str]], ...], searchTerms: List[Track]
    ) -> List[Track]:
        filteredFilesWMetadata: tuple[tuple[str, Path, dict[str, str]], ...] = tuple(
            filter(lambda x: x[2] is not None, filesWithMetadata)
        )

        # Index for faster lookup
        artist_track_map: dict[str, List[tuple[str, Path, dict[str, str]]]] = defaultdict(list)
        for item in filteredFilesWMetadata:
            name, path, metadata = item
            artist = metadata.get("artist", "").lower()

            if artist == "":
                continue
            artist_track_map[artist].append((name, path, metadata))

        remaining_tracks: List[Track] = []
        for term in searchTerms:
            found = False
            artist = term.artist.lower()

            if artist in artist_track_map:
                files = artist_track_map[artist]
                searchFiles = tuple(map(lambda x: (x[0], x[1]), files))
                idx = track_binary_search(sf(term.title), searchFiles)
                if idx is not None:
                    file = searchFiles[idx]
                    self.found_items.append(str(file[1]))
                    found = True

            if not found:
                for artistName, files in artist_track_map.items():
                    if horspool(artist, artistName):
                        searchFiles = tuple(map(lambda x: (x[0], x[1]), files))
                        idx = track_binary_search(sf(term.title), searchFiles)
                        if idx is not None:
                            file = searchFiles[idx]
                            self.found_items.append(str(file[1]))
                            found = True
                            break
            if not found:
                remaining_tracks.append(term)

        return remaining_tracks

    def _search_by_filename(self, files: tuple[tuple[str, Path], ...], searchTerms: List[Track]) -> List[Track]:
        remaining_tracks: List[Track] = []
        for term in reversed(searchTerms):
            idx = track_binary_search(sf(term.title), files)

            if idx is not None:
                file = files[idx]
                self.found_items.append(str(file[1]))
            else:
                remaining_tracks.append(term)

        return remaining_tracks

    def find_tracks(self, search_path: Path, use_metadata: bool = True) -> list[Track]:
        if not isinstance(search_path, Path):
            search_path = Path(search_path)

        if Playlist.files is not None:
            logger.info("Using static variable files")
            files = Playlist.files
        elif self.is_file_cache_valid():
            logger.info("Using cache")
            files = self.read_from_file_cache_db()
            Playlist.files = files
        else:
            logger.info("Cache invalid, searching for files")
            files = self._find_track_files(search_path)
            self.write_to_file_cache_db(files)

        logger.info(f"Found {len(files)} files")
        searchTerms = self.items.copy()

        if use_metadata:
            logger.info("Using metadata")
            filesWithMetadata = self._process_metadata(files)

            remaining = self._search_with_metadata(filesWithMetadata, searchTerms)
        else:
            logger.info("Not using metadata")
            remaining = self._search_by_filename(files, searchTerms)

        logger.info(f"Finished file search found {len(self.found_items)} out of {len(self.items)} tracks")
        return remaining

    def generate_m3u(
        self,
        save_path: Path,
        relative: bool = False,
        prefix: Optional[str] = None,
        root_path: Optional[Path] = None,
    ) -> None:
        if isinstance(save_path, str):
            save_path = Path(save_path)

        if len(self.found_items) == 0:
            raise RuntimeError("Cannot generate M3U with no files")
        if relative and root_path is None:
            raise RuntimeError("If relative is set to true a root_path must be suppiled")
        root_path = cast(Path, root_path)
        prefix = f"{prefix}_" if prefix else ""

        try:
            with open(
                save_path / f"{prefix}{sanitize_generated_playlist_name(self.name)}.m3u8", mode="+w", encoding="utf-8"
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
