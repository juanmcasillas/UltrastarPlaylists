#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# consolehelper.py
# 09/27/2023 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Implements a interactive console to do some manteinance task in the 
# ultrastar song database, and also allows to create playlists
#
# ############################################################################

import os
import code
import inspect
import ultrastar.literals
from ultrastar.helper import Helper

class ConsoleHelper(code.InteractiveConsole):
    def __init__(self, helper):
        self.helper = helper
        self.db = helper.db
        self.config = helper.config
        self.environment = None
        self.banner = None

        self.set_environment()
        self.set_banner()
        code.InteractiveConsole.__init__(self,locals=self.environment)

    def do_interact(self):
        self.interact(banner=self.banner)
       

    def set_banner(self):
        self.banner = []
        self.banner.append("-" * 80)
        self.banner.append(" UltraStar console")
        self.banner.append("-" * 80)
        self.banner.append("\n")
        self.banner.append("Commands")

        for entry,value in self.environment.items():
            try:
                sig = inspect.signature(value)
                doc = inspect.getdoc(value)

                func_full_name ="%s %s" % (entry, sig)
                func_doc_lines = list(map(lambda x: "\t%s" % x, doc.split(os.linesep))) # add tab to the line
                self.banner.append("\n")
                self.banner.append(func_full_name)
                self.banner.append("-" * len(func_full_name))
                self.banner += func_doc_lines
                self.banner.append("\n")
            except Exception as e:
                pass

        self.banner = os.linesep.join(self.banner)

    def set_environment(self):
        self.environment = {}
        self.environment["exit"] = ConsoleHelper.console_exit
        self.environment["get"] = self.console_get_input
        self.environment["fields"] = self.console_db_get_fields
        self.environment["commands"] = self.console_print_commands
        self.environment["set"] = self.console_db_set_field
        self.environment["refresh_db"] = self.console_db_refresh_db
        self.environment["create_playlist"] = self.console_create_playlist

        self.environment["seconds_to_str"] = Helper.seconds_to_str
        
        self.environment["db"] = self.console_get_db
        self.environment["LANGUAGES"] = self.console_get_LANGUAGES
        self.environment["EDITIONS"] = self.console_get_EDITIONS
        self.environment["GENRES"] = self.console_get_GENRES


    @staticmethod
    def console_exit():
        """exits from console

        Raises:
            SystemExit: Exist from interactive console
        """
        raise SystemExit
  
    
    def console_get_input(self, input):
        """if string, run the query and return the items, but if not, return the array

        Args:
            input (str / list): if str run the query, if list pass it

        Returns:
            list: the items
        """

        if isinstance(input, str):
            return self.console_db_get_results(input)
        return input


    def console_db_get_results(self, query):
        """execute a query in the database and returns it

        Args:
            query (str): sql valid query

        Returns:
            list: a list of dicts with the results
        """

        cursor = self.db.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        rows = list(map(lambda x: dict(x), rows))
        cursor.close()
        return rows

    def console_db_get_fields(self):
        """return the column names of the SONGS table

        Returns:
            list: a list of strings with the fields
        """

        cursor = self.db.cursor()
        cursor.execute("PRAGMA table_info(songs)");
        rows = cursor.fetchall()
        fields = []
        for i in rows:
            fields.append('%s (%s)' % (i[1], i[2]))
        return fields

    def console_print_commands(self):
        """print the command lists
        """
        print(self.banner)


    def console_db_set_field(self, input, field, value):
        """Update the song configuration changing a existing given attribute

        Args:
            input (str): the name of the field (see fields() for the list of the available fields)
            field (str): the value of the name (e.g. input=genre, field="Rock")
            value (str): the new value for the input (e.g. value="Pop")
        """
        
        items = self.console_get_input(input)

        cursor = self.db.cursor()
        for i in items:
            cursor.execute("update songs set %s=? where id=?" % field, [value,i['id']])
            # save file
            cursor.execute("select * from songs where id = ?", [i['id']])
            song = cursor.fetchone()
            if not song:
                print("warning, can't update song %s (%s:%s)" % (i['id'], field, value))
                continue
            self.helper.update_song_file(i['dirname'],field=field, value=value)
        cursor.close()

    def console_db_refresh_db(self):
        """Reloads the database from songs files"""
        self.helper.refresh_db()

    def console_create_playlist(self, input, name):
        """creates a new playlist file with the selection as input (list of songs or sql query)

        Args:
            input (str/list): sql query or list of songs dicts
            name (str): name of the playlist (valid filename)
        """
        items = self.console_get_input(input)
        cursor = self.db.cursor()
        songs = []
        for i in items:
            cursor.execute("select * from songs where id = ?", [i['id']])
            song = cursor.fetchone()
            songs.append({'artist': song['artist'], 'title': song['title']})
        self.helper.store_playlist(songs, name)

    
    def console_get_db(self):
        """Returns the database connection

        Returns:
            sqlconn: the database connection
        """
        return self.db

    def console_get_LANGUAGES(self):
        """get the available language list

        Returns:
            dict: a dict with the 'en' and 'es' language names
        """
        return ultrastar.literals.LANGUAGES

    def console_get_EDITIONS(self):
        """get available singstar editions

        Returns:
            list: a list with all the available singstar editions
        """
        return ultrastar.literals.EDITIONS

    def console_get_GENRES(self):
        """get available singstar genres

        Returns:
            list: a list with all the available singstar genres
        """
        return ultrastar.literals.GENRES

