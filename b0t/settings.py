#!/usr/bin/env python3
# encoding: utf-8

import re
import os
import sys
import syslog
import argparse
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Dict, Optional, Type, Set, Union

# Config sources. Order determines priority when it comes to overwriting
# (sources at the end of the list have higher priority)
# Available source types:
# -dict: converts dict into list of strings
# -os._Environ: finds keys matching {PROGRAM_NAME}_*, removes the prefix, and converts to lowercase
# -pathlib.Path: file is loaded. file takes the format:
#    key value
#    bool_key
# -list: consecutive keys, booleans and values. any non-string is converted to a string:
#    ['-v', '--key', 'value']
# -set: handled as a list
# -str: split into list by whitespace

class Settings:
	_parser: argparse.ArgumentParser
	_name: Optional[str]
	_config_path: Optional[Union[str, Path]]
	_config_path_arg: Optional[Union[str, Path]]
	_usage: Optional[str]
	_epilog: Optional[str]
	_settings: Dict[str, Any]
	_handlers: Dict[Type, Callable]
	sources: List[Union[dict, list, set, str, os._Environ, Path]]

	def __init__(self, sources: Optional[list] = None, name: Optional[str] = None, config_path: Optional[Union[str, Path]] = None) -> None:
		self._parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
		self._name = name
		self._config_path = config_path
		self._config_path_arg = None
		self._usage = None
		self._epilog = None
		self._settings = dict()
		self._handlers = {
			str: self._load_str,
			Set: self._load_list,
			list: self._load_list,
			dict: self._load_dict,
			Path: self._load_path,
			os._Environ: self._load_env
		}
		# Default sources are a config file in the home directory, a config file in the current directory, 
		# environmet variables, and then command line arguments (in order of ascending priority)
		self.sources = sources or [
			self.config_path,
			os.environ,
			sys.argv[1:]
		]
		# Alias to inner _parser.add_argument method
		self._parser.epilog = self.epilog

	def _log(self, msg, level: int = 1):
		syslog.syslog(level, msg)

	def _load_str(self, s: str) -> List[str]:
		return s.split()

	def _load_list(self, l: Union[list, set]) -> List[str]:
		return [str(x) for x in l]

	def _load_set(self, s: set) -> List[str]:
		return self._load_list(s)

	def _load_dict(self, d: dict) -> List[str]:
		args: List[str] = list()

		for item in d.items():
			key: str = str(item[0])
			value: str = str(item[1])
			key = '--' + key
			args.append(key)
			args.append(value)

		return args

	def _load_env(self, e: os._Environ) -> List[str]:
		args: List[str] = list()

		regex: re.Pattern = re.compile("^{}_".format(self.name.upper()))
		for (key, value) in e.items():
			if key.startswith(self.name.upper() + "_"):
				key = regex.sub("--", key).lower()
				args.append(key)
				args.append(value)

		return args

	def _load_path(self, p: Path) -> List[str]:
		args: List[str] = list()

		if p.is_file():
		    try:
		        text = p.read_text().strip()
		    except Exception as e:
		        self._log(f"Error loading file '{p}'")
		    else:
		        # Read each option line by line
		        for line in text.split('\n'):
		            line_parts = line.strip().split(maxsplit=1)
		            # Split the line at the first space and put
		            # a '--' before the first item to imitate
		            # command line option syntax
		            line_args = ['--' + line_parts[0], ' '.join(line_parts[1:])]
		            args.extend(line_args)

		return args

	def _load(self, sources: List[Union[dict, list, set, str, os._Environ, Path]] = list()) -> argparse.Namespace:
		args: List[str] = list()

		for source in sources:
			# Loop over the types in type_handlers to handle subclasses
			type_found: bool = False
			for item in self._handlers.items():
				item_type = item[0]
				if isinstance(source, item_type):
					type_found = True
					source_args: List[str] = self._handlers[item_type](source)
					args.extend(source_args)
					break
			if not type_found:
				self._log("No handler for source '{}'".format(str(source)[:20]))
		
		return self._parser.parse_known_args(args)

	def load(self, sources: List[Union[dict, list, set, str, os._Environ, Path]] = list()) -> None:
		if not sources:
			sources = self.sources
		for (key, value) in self._load(sources)._get_kwargs():
			# argparse stores key/value pairs in a list of tuples,
			# so to preserve priority order while creating a dictionary, we loop over those items
			self._settings[key] = value

	@property
	def name(self) -> str:
		"""Returns the program name (by default sys.argv[0]), keeping only letters and numbers, replacing spaces with underscores, and converting to lowercase. If sys.argv is empty, uses 'settingspy'"""
		if self._name == None:
			if len(sys.argv) < 1 or not sys.argv[0]:
				self._name = "settingspy"
			else:
				self._name = Path(sys.argv[0]).name
			self._name = re.sub('[^a-zA-Z0-9 ]+', '', self._name)
			self._name = self._name.replace(" ", "_")
		return str(self._name).lower()

	@name.setter
	def name(self, x: str) -> None:
		self._name = x

	@property
	def usage(self) -> Optional[str]:
		return self._usage

	@usage.setter
	def usage(self, x: str) -> None:
		self._usage = x
		self._parser.usage = x
	
	@property
	def epilog(self) -> str:
		if self._epilog:
			return self._epilog
		return f"""
You can set any of these options in a .{self.name}rc file
located in the home directory or the current directory.
You can also set environment variables that match {self.name.upper()}_OPTION

~/.{self.name}rc
  key value
  verbose

{self.name.upper()}_KEY=value python3 {self._name}"""

	@epilog.setter
	def epilog(self, x: str) -> None:
		"""The text to be displayed after the help message"""
		self._epilog = x
		self._parser.epilog = x

	@property
	def config_path(self) -> Optional[Union[str, Path]]:
		if self._config_path:
			return Path(self._config_path)
		# Look for a user defined config path
		if self._config_path_arg:
			self._config_path = self._config_path_arg
		else:
			config_name: str = ".{}rc".format(self.name)
			# Look for a config file in the current directory
			self._config_path = Path(config_name)
			if not self._config_path.is_file():
				# Look in the home directory
				self._config_path = Path.home().joinpath(config_name)
		return self._config_path

	@config_path.setter
	def config_path(self, x: Union[str, Path]) -> None:
		self._config_path = x
	
	def get(self, key: str = "", default: Any = None) -> Any:
		"""Returns the value of key. If key is not found, returns default."""
		if not key:
			return self._settings
		else:
			return self._settings.get(key, default)

	def set(self, key: str, value: Any) -> None:
		"""Sets key to value"""
		self._settings[key] = value

	def add_setting(self, *args, **kwargs) -> None:
		"""An alias to the internal argparse.ArgumentParser.add_argument. Adds an option action="load_config" to allow for specifying specific config filepaths"""
		is_config: bool = kwargs.get("action") == "load_config"
		if is_config:
			kwargs["action"] = "store"
		setting = self._parser.add_argument(*args, **kwargs)
		if is_config:
			self._config_path_arg = setting.dest
