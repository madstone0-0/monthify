# Utilities

import datetime
import re
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from monthify.protocols import Comparable


def extract_month_and_year(date: str) -> Tuple[str, str]:
    """Extract month and year from date string"""
    datem = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    year = datem.year
    month = datem.strftime("%B")
    return str(month), str(year)


def sort_chronologically(playlist_names: Iterable, reverse: bool = True) -> List[str]:
    """Sort months and years chronologically for playlist names"""
    sorted_list = sorted(
        playlist_names,
        key=lambda d: (d[1], datetime.datetime.strptime(d[0], "%B")),
        reverse=reverse,
    )
    return sorted_list


def format_playlist_name(month: str, year: str) -> str:
    return f"{month} '{year[2:]}"


def sanitize_generated_playlist_name(playlist_name: str) -> str:
    return playlist_name.strip().replace(" ", "_").replace("'", "").strip()


def normalize_text(text: str) -> bytes:
    """Normalize text to lowercase and replace non-ascii characters with xml entities"""
    return str(text).encode("utf-8", errors="xmlcharrefreplace").lower()


def conditional_decorator(dec, attribute):
    """
    Cache decorator wrapper to ensure fresh results if playlists have been created
    """

    def decorator(func):
        def wrapper(self):
            if getattr(self, attribute) is True:
                return func(self)
            return dec(func)(self)

        return wrapper

    return decorator


def str_is_greater(a: str, b: str) -> bool:
    """
    Compare two strings by summing their ascii values
    """
    if sum(ord(c) for c in a.lower()) > sum(ord(c) for c in b.lower()):
        return True
    return False


# Shift table cache for horspool's algorithm
shiftTableCache: dict[str, dict[str, int]] = defaultdict(dict)


def shift_table(pattern: str) -> dict[str, int]:
    """
    Generate shift table for Horspool's algorithm
    """
    m = len(pattern)
    table: dict[str, int] = defaultdict(lambda: m)
    for j in range(m - 1):
        table[pattern[j]] = m - 1 - j
    return table


def horspool(pattern: str, corpus: str) -> bool:
    """
    Implements Horspool's algorithm for string matching (Introduction to the Design and Analysis of Algorithms p. 262)
    """
    m = len(pattern)
    n = len(corpus)
    if m == 0 or n == 0:
        return False
    if m > n:
        return False

    if len(shiftTableCache[pattern]) == 0:
        table = shift_table(pattern)
        shiftTableCache[pattern] = table
    else:
        table = shiftTableCache[pattern]

    i = m - 1
    while i <= n - 1:
        k = 0
        while k <= m - 1 and pattern[m - 1 - k] == corpus[i - k]:
            k += 1
        if k == m:
            return True
        else:
            i += table[corpus[i]]
    return False


def relaxed_horspool(pattern: str, corpus: str) -> bool:
    clean_pattern = re.sub(r"[^\w\s]", "", pattern.lower())
    clean_corpus = re.sub(r"[^\w\s]", "", corpus.lower())
    return horspool(clean_pattern, clean_corpus)


def binary_search[T: Comparable](
    target: T, searchSpace: Sequence[T], comparator: Callable[[T, T], bool] = lambda x, y: x > y
) -> Optional[int]:
    low = 0
    high = len(searchSpace) - 1
    while low < high:
        midIdx = (high + low) // 2
        mid = searchSpace[midIdx]
        if mid == target:
            return midIdx
        elif comparator(mid, target):
            high = midIdx - 1
        else:
            low = midIdx + 1
    return None


TRACK_SAN_REGEXES = [
    re.compile(r"^\d{1,}\-"),
    re.compile(r"^\d{1,}(\-\d{1,})?"),
    re.compile(r"^\d{1,} "),
    re.compile(r"^# - "),
]


def sanitize_filename(track: str) -> str:
    sanitized = track
    if any([regex.fullmatch(sanitized) is not None for regex in TRACK_SAN_REGEXES]):
        return sanitized

    for regex in TRACK_SAN_REGEXES:
        sanitized = re.sub(regex, "", sanitized)
    return normalize_text(sanitized).strip().decode()


def track_binary_search(target: str, searchSpace: tuple[tuple[str, Path], ...]) -> Optional[int]:
    low = 0
    high = len(searchSpace) - 1
    targetText = target.lower()
    while low <= high:
        midIdx = (high + low) // 2
        mid = searchSpace[midIdx]
        midText = mid[0].lower()
        longer = midText if len(midText) > len(targetText) else targetText
        shorter = midText if longer == targetText else targetText
        if midText == targetText:
            return midIdx
        elif horspool(shorter, longer):
            return midIdx
        elif relaxed_horspool(shorter, longer):
            return midIdx
        elif targetText < midText:
            high = midIdx - 1
        else:
            low = midIdx + 1
    return None
