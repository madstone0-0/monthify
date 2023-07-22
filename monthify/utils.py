# Utilities

import datetime
from typing import Iterable, List, Tuple


def extract_month_and_year(date: str) -> Tuple[str, str]:
    """Extract month and year from date string"""
    datem = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    year = datem.year
    month = datem.strftime("%B")
    return str(month), str(year)


def sort_chronologically(playlist_names: Iterable) -> List[str]:
    """Sort months and years chronologically for playlist names"""
    sorted_list = sorted(
        playlist_names,
        key=lambda d: (d[1], datetime.datetime.strptime(d[0], "%B")),
        reverse=True,
    )
    return sorted_list


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


def strIsGreater(a: str, b: str) -> bool:
    """
    Compare two strings by summing their ascii values
    """
    if sum(ord(c) for c in a.lower()) > sum(ord(c) for c in b.lower()):
        return True
    return False


def search_normalized(dataset: Iterable[str], target: str) -> bool:
    """
    Binary search for target in dataset
    """
    low = 0
    high = len(dataset) - 1
    sorted_dataset = sorted(dataset, key=lambda a: sum(ord(c) for c in a.lower()))

    while low <= high:
        mid = (high + low) // 2
        guess = sorted_dataset[mid]

        if normalize_text(guess) == normalize_text(target):
            return True

        if strIsGreater(guess, target):
            high = mid - 1
        else:
            low = mid + 1

    return False
