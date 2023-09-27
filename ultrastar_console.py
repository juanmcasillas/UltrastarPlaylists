#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# ultrastar_console.py
# 09/27/2023 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Manages and generates the configuration list for UltraStar songs, and
# provides a console to launch sql commands in order to generate playlist
# and so on
#
# ############################################################################

import argparse
from ultrastar.appenv import AppEnv
from ultrastar.songhelper import UltraStarHelper
from ultrastar.consolehelper import ConsoleHelper
import sys


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-r", "--restore-backup", help="Restore from backup config files", action="store_true")
    parser.add_argument("-d", "--delete-backup", help="Also delete backup files", action="store_true")
    parser.add_argument("-c", "--console", help="Start the interactive console", action="store_true")
    parser.add_argument("config_file", help="Configuration File")
    args = parser.parse_args()

    AppEnv.config(args.config_file)
    AppEnv.config_set("verbose",args.verbose)
    AppEnv.print_config()

    ultrastar_helper = UltraStarHelper(AppEnv.config())

    if args.restore_backup:
        print("Restoring configuration from backup")
        ultrastar_helper.restore_backup(args.delete_backup)
        sys.exit(0)

    ultrastar_helper.load_db()
    ultrastar_helper.test_db()

    # prepare console and run it with the data.
 
    if args.console:
        try:
            ConsoleHelper(ultrastar_helper).do_interact()
        except SystemExit:
            pass
    
    ultrastar_helper.shutdown()

    # get("select id,title from songs where genre='UNKNOWN'")
    # get("select id,title from songs where edition='UNKNOWN'")
    # set_edition(get("select * from songs where edition='UNKNOWN'"),"Sin Edición")
    # set_genre(get("select * from songs where genre='UNKNOWN'"),"Pop")
    # create_playlist("select id from songs where genre='Pop'", "mypop")
    # create_playlist(get("select id from songs where genre='Pop'"), "mypop")