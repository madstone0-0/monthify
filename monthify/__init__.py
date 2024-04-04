import sys
from os import makedirs

from appdirs import user_config_dir, user_data_dir
from loguru import logger
from rich.console import Console

ERROR = "bold red"
SUCCESS = "bold green"

console = Console()

appname = "Monthify"
appauthor = "madstone0-0"
appdata_location = user_data_dir(appname, appauthor)

makedirs(f"{appdata_location}/logs", exist_ok=True)
logLocation = f"{appdata_location}/logs"
logger.add(sys.stderr, format="{time} {level} {message}", filter="monthify", level="INFO")
logger.remove()
logger.add(f"{logLocation}/monthify.log", rotation="00:00", compression="zip")
logger.add(f"{logLocation}/error.log", filter=lambda r: r["level"].name == "ERROR", mode="w")
logger.add(f"{logLocation}/info.log", filter=lambda r: r["level"].name == "INFO", mode="w")
logger.add(f"{logLocation}/debug.log", filter=lambda r: r["level"].name == "DEBUG", mode="w")


if sys.platform == "win32" or sys.platform == "darwin":
    appconfig_location = appdata_location
else:
    appconfig_location = user_config_dir(appname.lower(), appauthor)
