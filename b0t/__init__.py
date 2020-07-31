1#!/usr/bin/env python3
# encoding: utf-8

import re
import os
import sys
import discord
import argparse
from pathlib import Path

# Get the program name, 
# keeping only letters and numbers,
# replacing spaces with underscores,
# and converting to lowercase
# (to be used for the config filepath and env variables)
PROGRAM_NAME = sys.argv[0]
PROGRAM_NAME = re.sub('[^a-zA-Z0-9 ]+', '', PROGRAM_NAME)
PROGRAM_NAME = PROGRAM_NAME.replace(" ", "_")
PROGRAM_NAME = PROGRAM_NAME.lower()

# Enable newlines in the epilog
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-i", "--id", help="discord app id",
                    action="store_true")
parser.add_argument("-s", "--secret", help="discord app secret",
                    action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-c", "--config", help="path to configuration json file",
                    action="store_true")
parser.epilog = """
You can set any of these options in a ~/.{prog}rc json
file located in your home directory or by setting
a {prog_upper}_OPTION environment variable. EG:

~/.{prog}rc
  id 1234567890
  secret abcdefg
  verbose

{prog_upper}_ID=1234567890 {prog_upper}_SECRET=abcdefg python3 {prog_og}
""".format_map({
    "prog": PROGRAM_NAME,
    "prog_upper": PROGRAM_NAME.upper(),
    "prog_og": sys.argv[0]
})

# Collect any config file arguments before parsing args
config_path = Path.home().joinpath(".b0trc")
# Load if it exists
config_args = list()
if config_path.is_file():
    try:
        config_text = config_path.read_text().strip()
    except Exception as e:
        pass
    else:
        # Read each option line by line
        for line in config_text.split('\n'):
            line = line.strip().split(maxsplit=1)
            # Split the line at the first space and put
            # a '--' before the first item to imitate
            # command line option syntax
            line_args = ['--' + line[0], ' '.join(line[1:])]
            config_args.extend(line_args)

# Collect any environment variables that match {prog}_*
env_args = list()
for env_arg in filter(lambda x: x.startswith(PROGRAM_NAME.upper() + "_"), os.environ):
    # Remove the program name from the arg and lowercase
    env_arg_fixed = env_arg[len(PROGRAM_NAME) + 1:].lower()
    env_args.append('--' + env_arg_fixed)
    env_args.append(os.environ.get(env_arg))

# Finally, parse the args in order of priority
print('config_args', config_args)
print('env_args', env_args)
print('sys_args', sys.argv[1:])
args = parser.parse_args(config_args + env_args + sys.argv[1:])

# Log command
DEBUG = True

## Get client auth
# check environment
DISCORD_AUTH_ID = os.environ.get('DISCORD_AUTH_ID')
DISCORD_AUTH_SECRET = os.environ.get('DISCORD_AUTH_SECRET')
# check home folder
if not DISCORD_AUTH_ID or not DISCORD_AUTH_SECRET:
    from pathlib import Path
    auth_filepath = Path.home().joinpath("")