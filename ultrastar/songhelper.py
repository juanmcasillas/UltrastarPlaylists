#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# ultrastar_helper.py
# 09/27/2023 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# helper to load and store the ultrastar son files into a sql database
#
# ############################################################################


import os
from collections import namedtuple
import sqlite3
import shutil
import mutagen.mp3


from .appenv import AppEnv
from .literals import *
from .helper import Helper

SongInfo = namedtuple('SongInfo', ['config','is_multi', 'dirname' ])

class UltraStarHelper:
    def __init__(self, config):
        self.config = config
        self.verbose = self.config.verbose
        self.db = None


    def test_db(self):
        """shows the database contents
        """
        cursor = self.db.cursor()
        cursor.execute("select * from songs;")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))

        print("----")
        cursor.execute("select * from multi;")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        
        cursor.close()
        


    def create_tables(self):
        """
        {'title': "It's Not Unusual", 'artist': 'Tom Jones',
        'language': 'English', 'edition': 'SingStar Pop', 'genre': 
        'Misc', 'year': '1964', 'mp3': 
        "Tom Jones - It's Not Unusual.mp3", 
        'cover': "Tom Jones - It's Not Unusual [CO].jpg", 
        'video': "Tom Jones - It's Not Unusual [VD#0].avi", 
        'videogap': '0', 'bpm': '322', 'gap': '11133,54'}
        """
        sql_prologue = [
            "drop table if exists songs;",
            "drop table if exists multi;"
        ]
        sql_epilogue = []

        sql_songs = """
        create table songs(
            id integer primary key AUTOINCREMENT,
            title text not null,
            artist text not null,
            language text not null,
            edition text not null,
            genre text not null,
            year integer not null,
            mp3 text not null,
            cover text not null,
            video text not null,
            videogap integer not null,
            bpm real not null,
            gap real not null,
            path text not null,
            dirname text not null,
            duration timestamp not null default 0,
            multi integer not null default 0
        );
        """
        sql_multi = """
        create table multi(
            id integer primary key AUTOINCREMENT,
            song_id integer not null,
            player text not null,
            singer text not null,
            FOREIGN key(song_id) references SONGS(id)
        );
        """
        cursor = self.db.cursor()

        for sql_sentence in sql_prologue:
            cursor.execute(sql_sentence)
        
        cursor.execute(sql_songs)
        cursor.execute(sql_multi)
        
        for sql_sentence in sql_epilogue:
            cursor.execute(sql_sentence)
        
        cursor.close()


    def insert_into_db(self,items):
        """
        inserts data into the database. if Items is dict, insert it, else
        iterate the list of dicts.
        """

        sql_insert_songs = """
        insert into SONGS(title, artist, language, edition, genre, year,
                        mp3, cover, video, videogap, bpm, gap, 
                        path, dirname, duration, multi) 
                values ( ?, ?, ?, ?, ?, ?, 
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ? );
        """

        sql_insert_players = """
        insert into MULTI(song_id, player, singer) values ( ?, ?, ? );
        """

        cursor = self.db.cursor()

        item_list = []
        if isinstance(items,dict):
            item_list.append(dict)
        else:
            item_list = items

        for item in item_list:
            cursor.execute(sql_insert_songs, (item['title'], item['artist'],
                                            item['language'], 
                            item['edition'], item['genre'], item['year'],
                            item['mp3'],item['cover'],item['video'],
                            item['videogap'],item['bpm'],item['gap'],
                            item['path'], item['dirname'],
                            item['duration'], item['multi'] ))

            id = cursor.lastrowid
            for key in item['players']:
                val = item['players'][key]
                cursor.execute(sql_insert_players,(id, key, val))
        
        cursor.close()


    def store_in_db(self, config, refresh=False, init=True):
        """stores configuration in a SqlLite Database, can be on memory or persistent (disk)

        Args:
            config (list): list the songs configuration
            refresh (bool, optional): if true, drop data and reload database and create it again. Defaults to False.
            init (bool, optional): if true, create the database

        """

        if not refresh:
            # allways use db file
            #if self.config.read_from_db:
            self.db = sqlite3.connect(self.config.dbfile, check_same_thread=False)
            #else:
            #self.db = sqlite3.connect('file:cachedb?mode=memory&cache=shared', check_same_thread=False)
            self.db.row_factory = sqlite3.Row 
        else:
            # don't modify the database
            self.db.row_factory = sqlite3.Row 
        
        if init and not self.config.read_from_db:
            self.create_tables()
            self.insert_into_db(config)
            if self.verbose > 1:
                print("%d records inserted in DB" % len(config))
        
        self.db.commit()

    
    def restore_backup(self, delete_backup=False):
        """restores the backup file to revert the situation

        Args:
            delete_backup (bool, optional): if true, deletes the back files. Defaults to False.
        """

        for entry in os.listdir(self.config.full_songs_dir):
        
            full_path = os.path.sep.join([self.config.full_songs_dir, entry])
            if not os.path.isdir(full_path):
                continue

            # process only entries here.
            # check if there is a [MULTI] entry (duet) or single.
            song_config = "%s" % os.path.sep.join( [ full_path, entry ] )
            song_config_multi = "%s [MULTI]" % song_config
            song_config = "%s.txt" % song_config
            song_config_multi = "%s.txt" % song_config_multi

            song_config_bck = "%s.bak" % song_config
            song_config_multi_bck = "%s.bak" % song_config_multi

            if os.path.exists(song_config_bck):
                shutil.copy2(song_config_bck, song_config) 
                if self.verbose > 1:
                    print("restoring: %s" % song_config)
                if delete_backup:
                    os.remove(song_config_bck)
                    if self.verbose > 1:
                        print("deleting backup file : %s" % song_config_bck)

            if os.path.exists(song_config_multi_bck):
                shutil.copy2(song_config_multi_bck, song_config_multi) 
                if self.verbose > 1:
                    print("restoring: %s" % song_config_multi)
                if delete_backup:
                    os.remove(song_config_multi_bck)
                    if self.verbose > 1:
                        print("deleting backup file : %s" % song_config_multi_bck)


    def add_tags(self, tags, data, fname):
        """add the missing tags to the song configuration file

        Args:
            tags (dict): dict with the tags (name, value)
            data (text): the configuration file data
            fname (str): the song's configuration file
        """

        # is not multi, so go out
        if not fname: 
            return 

        for item in tags:
            tag, value = item
            entry = "#%s:%s\n" % (tag.upper(), value)
            data = entry + data

        Helper.do_backup(fname)
        with open(fname, 'w', encoding=self.config.encoding) as f:
            f.write(data)



    def merge_config(self, config, config_multi, dirname, path):
        """merge the multi (duet) configuration with the single one, to get all the data

        Args:
            config (dict): dict with the single config
            config_multi (dict): dict with the duet (multi) config
            dirname (str): the dirname of the song
            path (str): full path of the configuration file for the song

        Returns:
            dict: merged dict.
        """
        players = {}
        is_multi = 0
        if config_multi:
            for item in config_multi.keys():
                if item.startswith('duetsinger'):
                    is_multi = 1
                    entry = item.replace('duetsinger','')
                    players[entry] = config_multi[item]

        filename_mp3 = os.path.sep.join([dirname,config['mp3']])
        
        # add synthetic fields

        config['players'] = players
        config['path'] = path
        config['dirname'] = dirname
        config['duration'] = 0
        
        if os.path.exists(filename_mp3):
            try:
                config['duration'] = mutagen.mp3.MP3(filename_mp3).info.length
            except Exception as e:
                print("Warning: %s on %s" % (e, filename_mp3))
                      
        config['multi'] = is_multi
        return config


    def get_songs(self, dirname):
        """retrieve the list of songs in the filesystem

        Args:
            dirname (str): the full path to the song directory

        Returns:
            list: List of SongInfo
        """

        songs = []
        for entry in os.listdir(dirname):
        
            full_path = os.path.sep.join([dirname, entry])
            if not os.path.isdir(full_path):
                continue

            # process only entries here.
            # check if there is a [MULTI] entry (duet) or single.
            song_config = "%s" % os.path.sep.join( [ full_path, entry ] )
            song_config_multi = "%s [MULTI]" % song_config
            song_config = "%s.txt" % song_config
            song_config_multi = "%s.txt" % song_config_multi

            if not os.path.exists(song_config):
                if self.verbose > 0:
                    print("Warning: '%s' has no config" % entry)
                continue

            if not os.path.exists(song_config_multi):
                song_config_multi = None

            songs.append( SongInfo(config=song_config,
                                is_multi=song_config_multi,
                                dirname=full_path)
                        )
        return songs


    def read_config(self, data, fname):
        """
        Read the config from the songs configuration file.
        #TITLE:Human
        #ARTIST:The Killers
        #LANGUAGE:English
        #EDITION:SS Pop 2009
        #YEAR:2008
        #MP3:The Killers - Human.mp3
        #COVER:The Killers - Human.jpg
        #VIDEO:The Killers - Human.avi
        #VIDEOGAP:0
        #BPM:268,04
        #GAP:12983,14
        #GENRE?
        """
        config = {}
        tags = []
        for l in data.split('\n'):
            if l.startswith('#'):
                args = l[1:].split(':')
                command = args[0]
                value = "".join(args[1:])
                # convert decimal comma separated numbers to real ones.

                if command.lower() in [ "bpm", "videogap" ]:
                    value = value.replace(',','.')

                config[command.lower()] = value
                
            else:
                break
        
        if len(config.keys()) == 0:
            if self.verbose > 1:
                print("can't read configuration from file: %s (corrupt data?)" % fname)
                return None, None

        # check for missing tags:

        required_tags = [ 'title', 'artist', 'language', 'edition',
                          'genre', 'year', 'mp3', 'cover', 'video',
                          'videogap', 'bpm', 'gap' ]


        for tag in required_tags:
            if not tag in config.keys():
                tag_missing_value = "UNKNOWN"
                if tag in [ 'genre', 'edition', 'language', 'artist', 'title']:
                    if self.verbose > 0:
                        print("tag %s is missing on file %s" % (tag, fname))
                    tags.append( (tag, tag_missing_value) )
                if tag in [ 'videogap', 'gap' ]:
                    tag_missing_value = 0
                config[tag] = tag_missing_value
                
        return config, tags


    def process_songs(self,songs):
        """read the config of the songs and build the detailed configuration using dicts

        Args:
            songs (list): list of SongInfo

        Returns:
            list: list of dicts with the configuration values for the songs
        """
        data = []

        for song in songs:
            
            text = None
            text_multi = None
            config = None
            config_multi = None

            with open(song.config,'r', encoding=self.config.encoding) as f:
                text = f.read()
                config, tags = self.read_config(text, song.config)

            if tags:
                self.add_tags(tags, text, song.config)

            if song.is_multi:

                with open(song.is_multi,'r', encoding=self.config.encoding) as f:
                    text_multi = f.read()
                    config_multi,tags = self.read_config(text_multi, song.is_multi)

                    if tags:
                        self.add_tags(tags, text_multi, song.is_multi)


            if config:
                config = self.merge_config(config, config_multi, song.dirname, song.config)       
                data.append(config)

        return data


    def refresh_db(self):
        """
            Refresh the database (load the values again into the database from the file)
        """
        songs = self.get_songs(self.config.full_songs_dir)
        config = self.process_songs(songs)
        self.store_in_db(config, refresh=True)


    def load_db(self):
        """
            load the database
        """
        config = []
        if not self.config.read_from_db:
            songs = self.get_songs(self.config.full_songs_dir)
            config = self.process_songs(songs)
            if self.verbose > 0:
                print("initializing db from song files")

        self.store_in_db(config)




    def store_playlist(self, songs, name):
        """stores a list of songs as a playlist in ultrastar format

        Args:
            songs (list): the list of songs
            name (str): name of the playlist
        """
        text = []
        text.append('#Name: %s' % name)
        text.append('#Songs:')
        
        for song in songs:
            text.append("%s : %s" % (song['artist'], song['title']))
        
        filename = os.path.sep.join([self.config.full_playlist_dir, "%s.upl" % name])
        Helper.do_backup(filename)
        with open(filename, 'w', encoding=self.config.encoding) as f:
            f.write("\n".join(text))

        if self.verbose > 1:
            print("Playlist %s created with %d songs" % (name, len(songs)))


    def shutdown(self):
        """ends the execution, closes the database
        """
        self.db.close()
        raise SystemExit
    


    def update_config(self, filename, field, newvalue):
        """update the song config, changing the given field to the required value

        Args:
            filename (str): path for song configuration file
            field (str): the field name
            newvalue (str): the new value for the field
        """
        
        new_file = []
        with open(filename,'r', encoding=self.config.encoding) as f:
            text = f.read()
            for l in text.split('\n'):
                if l.startswith('#'):
                    args = l[1:].split(':')
                    command = args[0]
                    value = "".join(args[1:])
                    # if found the required field:
                    if command.lower() == field.lower():
                        
                        if command.lower() in [ "bpm", "videogap" ]:
                            newvalue = value.replace('.',',')
                        
                        new_line="#%s:%s" % (field.upper(),newvalue)
                        new_file.append(new_line)
                    else:
                        new_file.append(l)
                else:
                    new_file.append(l)
        
        Helper.do_backup(filename)
        with open(filename, 'w', encoding=self.config.encoding) as f:
            f.write("\n".join(new_file))    
        

    def update_song_file(self, song_dirname, field, value):
        """updates the song config (all the files) with the new value for the field

        Args:
            song_dirname (str): songs' directory
            field (str): the name of the field being changed
            value (str): the new value
        """

        path = os.path.dirname(song_dirname)
        entry = os.path.basename(song_dirname)
        
        song_config = "%s" % os.path.sep.join( [ song_dirname, entry ] )
        song_config_multi = "%s [MULTI]" % song_config
        song_config = "%s.txt" % song_config
        song_config_multi = "%s.txt" % song_config_multi

        if os.path.exists(song_config):
            self.update_config(song_config, field, value)
        
        if os.path.exists(song_config_multi):
            self.update_config(song_config_multi, field, value)
        
