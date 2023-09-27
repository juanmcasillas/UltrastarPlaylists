#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# appenv.py
# 09/27/2023 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Creates a global object with the configuration and some global elements
# if needed, to avoid the use of globals in the configuration.
#
# ############################################################################

import json
import os
import os.path

class AppEnvConfig:
    "must match exactly the json file"
    def __init__(self, **kwargs):

        self.verbose = 0
        self.github_url = "https://github.com/juanmcasillas/UltrastarPlaylists"
        self.read_from_db = False
        self.persistent = False
        self.do_backup = True
        self.dbfile = "songs.db"
        self.encoding = "iso-8859-15"

        if kwargs:
            for key,value in kwargs.items():
                self.__dict__[key] = value

    def validate(self):

        self.full_songs_dir = os.path.sep.join([self.ultrastar_dir, self.songs_dir])
        self.full_playlist_dir = os.path.sep.join([self.ultrastar_dir, self.playlist_dir])



class AppEnv:
    __conf = AppEnvConfig() # default init

    @staticmethod
    def config(fname=None):
        if not fname:
            return AppEnv.__conf
        else:
            try:
                with open(fname) as json_data_file:
                    data = json.load(json_data_file)
                    #data = json.load(json_data_file, object_hook=lambda d: SimpleNamespace(**d))
                    AppEnv.__conf = AppEnvConfig(**data)
                    AppEnv.__conf.validate()
                    AppEnv.__conf.config_dir = os.path.dirname(fname)
                    AppEnv.__conf.config_file = os.path.basename(fname)
                    return AppEnv.__conf
            except Exception as e:
                raise Exception(e) from e
    
    @staticmethod
    def config_set(var, value):
        AppEnv.__conf.__dict__[var] = value
        return AppEnv.__conf
    
    @staticmethod
    def print_config():
        print("AppEnv Configuration")
        for i in AppEnv.__conf.__dict__.keys():
            print("  %s: %s" % (i, AppEnv.__conf.__dict__[i]))
    
def APPENVCONFIG():
    "syntactic sugar for the other modules"
    return AppEnv.config()


def test_config():

    APPENVCONFIG()
    AppEnv.config("config/test_config.cfg")
    AppEnv.print_config()

if __name__ == "__main__":

    test_config()