#!python3
# Month and year parser

import datetime


def extract_month_and_year(date) -> (str, str):
    datem = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    year = datem.year
    month = datem.strftime("%B")
    return str(month), str(year)


def sort_chronologically(playlist_names) -> list[str]:
    sorted_list = sorted(playlist_names, key=lambda d: (d[1], datetime.datetime.strptime(d[0], "%B")), reverse=True)
    return sorted_list
