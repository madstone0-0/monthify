from uuid import uuid4

date_data = [
    ("2022-11-23T02:04:46Z", ("November", "2022")),
    ("2022-12-12T02:04:46Z", ("December", "2022")),
    ("2012-01-12T02:04:46Z", ("January", "2012")),
    ("2003-06-12T02:04:46Z", ("June", "2003")),
    ("1937-03-12T02:04:46Z", ("March", "1937")),
    ("1537-03-12T02:04:46Z", ("March", "1537")),
    ("2037-12-12T02:04:46Z", ("December", "2037")),
]

mock_data = {
    "username": {
        "display_name": "Hudson",
        "id": "8vx0z9rwpse4fzr62po8sca1r",
        "uri": "spotify:user:8vx0z9rwpse4fzr62po8sca1r",
    },
    "playlists": {
        "items": [{"name": "December '20", "id": f"{uuid4()}"}, {"name": "August '23", "id": f"{uuid4()}"}],
        "next": None,
    },
    "tracks": {
        "items": [
            {
                "added_at": "2023-08-01T19:48:57Z",
                "track": {
                    "id": "2Jkk7UunDLmtxSeHTgar4Z",
                    "name": "F.V.K. (Fearless Vampire Killers)",
                    "uri": "spotify:track:2Jkk7UunDLmtxSeHTgar4Z",
                },
            },
            {
                "added_at": "2023-07-29T08:44:20Z",
                "track": {
                    "id": "0YnP5BtP6lTwQV8gLOzaov",
                    "name": "Banned in D.C.",
                    "uri": "spotify:track:0YnP5BtP6lTwQV8gLOzaov",
                },
            },
            {
                "added_at": "2023-07-22T19:38:08Z",
                "track": {
                    "id": "3If9Idk1rglOqubIsJcpmv",
                    "name": "In The Garage",
                    "uri": "spotify:track:3If9Idk1rglOqubIsJcpmv",
                },
            },
        ],
        "next": None,
    },
}

dataset = [
    "December '20",
    "August '20",
    "February '20",
    "July '21",
    "May '20",
    "April '20",
    "October '21",
    "March '22",
    "December '19",
    "January '22",
    "August '22",
    "May '22",
    "September '22",
    "February '22",
    "November '20",
    "June '20",
    "March '21",
    "July '22",
    "January '21",
    "August '21",
    "September '21",
    "May '21",
    "April '22",
    "December '21",
    "November '19",
    "February '21",
    "July '20",
    "October '20",
    "November '22",
    "June '22",
    "April '21",
    "January '20",
    "March '20",
    "November '21",
    "June '21",
    "September '20",
    "October '22",
]

search_data = [
    (dataset, "October '22", True),
    (dataset, "October '21", True),
    (dataset, "October '27", False),
    (dataset, "Middd", False),
    (dataset, "😭", False),
]

playlist_data = [
    (
        [
            ("December", "2020"),
            ("August", "2020"),
            ("February", "2020"),
            ("July", "2021"),
            ("May", "2020"),
            ("April", "2020"),
            ("October", "2021"),
            ("March", "2022"),
            ("December", "2019"),
            ("January", "2022"),
            ("August", "2022"),
            ("May", "2022"),
            ("September", "2022"),
            ("February", "2022"),
            ("November", "2020"),
            ("June", "2020"),
            ("March", "2021"),
            ("July", "2022"),
            ("January", "2021"),
            ("August", "2021"),
            ("September", "2021"),
            ("May", "2021"),
            ("April", "2022"),
            ("December", "2021"),
            ("November", "2019"),
            ("February", "2021"),
            ("July", "2020"),
            ("October", "2020"),
            ("November", "2022"),
            ("June", "2022"),
            ("April", "2021"),
            ("January", "2020"),
            ("March", "2020"),
            ("November", "2021"),
            ("June", "2021"),
            ("September", "2020"),
            ("October", "2022"),
        ],
        [
            ("November", "2022"),
            ("October", "2022"),
            ("September", "2022"),
            ("August", "2022"),
            ("July", "2022"),
            ("June", "2022"),
            ("May", "2022"),
            ("April", "2022"),
            ("March", "2022"),
            ("February", "2022"),
            ("January", "2022"),
            ("December", "2021"),
            ("November", "2021"),
            ("October", "2021"),
            ("September", "2021"),
            ("August", "2021"),
            ("July", "2021"),
            ("June", "2021"),
            ("May", "2021"),
            ("April", "2021"),
            ("March", "2021"),
            ("February", "2021"),
            ("January", "2021"),
            ("December", "2020"),
            ("November", "2020"),
            ("October", "2020"),
            ("September", "2020"),
            ("August", "2020"),
            ("July", "2020"),
            ("June", "2020"),
            ("May", "2020"),
            ("April", "2020"),
            ("March", "2020"),
            ("February", "2020"),
            ("January", "2020"),
            ("December", "2019"),
            ("November", "2019"),
        ],
    ),
    (
        [
            ("November", "2019"),
            ("May", "2021"),
            ("February", "2022"),
            ("July", "2020"),
            ("June", "2020"),
            ("November", "2022"),
            ("August", "2034"),
            ("May", "1543"),
        ],
        [
            ("August", "2034"),
            ("November", "2022"),
            ("February", "2022"),
            ("May", "2021"),
            ("July", "2020"),
            ("June", "2020"),
            ("November", "2019"),
            ("May", "1543"),
        ],
    ),
]

text_data = [
    (
        "Oh chale it couldnt be that bad 😭",
        b"oh chale it couldnt be that bad \xf0\x9f\x98\xad",
    ),
    (
        "😃😢😅😞👌🏼😝😆👌👌Balls",
        b"\xf0\x9f\x98\x83\xf0\x9f\x98\xa2\xf0\x9f\x98\x85\xf0\x9f\x98\x9e\xf0\x9f\x91\x8c\xf0\x9f\x8f\xbc\xf0\x9f"
        b"\x98\x9d\xf0\x9f\x98\x86\xf0\x9f\x91\x8c\xf0\x9f\x91\x8cballs",
    ),
    (
        "ði ıntəˈnæʃənəl fəˈnɛtık əsoʊsiˈeıʃn",
        b"\xc3\xb0i \xc4\xb1nt\xc9\x99\xcb\x88n\xc3\xa6\xca\x83\xc9\x99n\xc9\x99l "
        b"f\xc9\x99\xcb\x88n\xc9\x9bt\xc4\xb1k \xc9\x99so\xca\x8asi\xcb\x88e\xc4\xb1\xca\x83n",
    ),
    (
        "‚deutsche‘ „Anführungszeichen“",
        b"\xe2\x80\x9adeutsche\xe2\x80\x98 \xe2\x80\x9eanf\xc3\xbchrungszeichen\xe2\x80\x9c",
    ),
]
