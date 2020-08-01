1#!/usr/bin/env python3
# encoding: utf-8

import sys
import discord
from .settings import Settings

# Setup settings
settings: Settings = Settings(name=__package__)
settings.add_setting("-i", "--id", help="discord app id")
settings.add_setting("-s", "--secret", help="discord app secret")
settings.add_setting("-c", "--config", help="path to configuration json file", action="load_config")
settings.add_setting("-v", "--verbose", help="increase output verbosity", action="store_true")
settings.load()

print(settings._settings)
print(sys.argv)