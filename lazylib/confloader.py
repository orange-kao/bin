#!/usr/bin/python3

import sys
import os
import configparser

class LazyConfigLoader:
    @staticmethod
    def str_to_bool(s):
        t = s.lower()
        if t == "true":
            return True
        elif t == "false":
            return False
        elif t == "none":
            return None
        return(s)

    @staticmethod
    def get_config(dir_name):
        home_dir = os.getenv("HOME")
        scr_basename = os.path.basename(sys.argv[0])
        conf_filename = os.path.join(home_dir, dir_name, f"{scr_basename}.ini")

        if os.path.isfile(conf_filename) is not True:
            raise RuntimeError(f"Config {conf_filename} does not exist")

        config = configparser.ConfigParser()
        config.read(conf_filename)

        ret_dict = {}

        for section in config.sections():
            ret_dict[section] = {}
            for key in config[section]:
                value = LazyConfigLoader.str_to_bool(config[section][key])
                ret_dict[section][key] = value

        return ret_dict

