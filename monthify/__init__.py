import sys

from appdirs import user_config_dir, user_data_dir
from rich.console import Console

ERROR = "bold red"
SUCCESS = "bold green"

console = Console()

appname = "Monthify"
appauthor = "madstone0-0"
appdata_location = user_data_dir(appname, appauthor)

if sys.platform == "win32" or sys.platform == "darwin":
    appconfig_location = appdata_location
else:
    appconfig_location = user_config_dir(appname.lower(), appauthor)
