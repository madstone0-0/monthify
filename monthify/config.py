import sys

import toml

from monthify import ERROR, appconfig_location, console

CONFIG_FILE_NAME = "monthify.toml"


class Config:
    def __init__(self) -> None:
        self.config = None
        self.using_config_file = False

    def get_config(self):
        try:
            with open(
                f"{appconfig_location}/{CONFIG_FILE_NAME}", "r", encoding="utf-8"
            ) as config_file:
                self.using_config_file = True
                self.config = toml.load(config_file)
        except FileNotFoundError:
            self.using_config_file = False
        except toml.TomlDecodeError:
            console.print("Invalid config document", style=ERROR)
            sys.exit(1)
        return self.config

    def is_using_config_file(self):
        return self.using_config_file
