#!python3
# Month and year parser

import datetime


def extract_month_and_year(date) -> (str, str):
    datem = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    year = datem.year
    month = datem.strftime("%B")
    return str(month), str(year)