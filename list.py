import glob
import argparse
import os
from collections import namedtuple
import sqlite3
import code
import shutil
import datetime

from literals import *

import mutagen.mp3

# example run 
# C:\software\python311\python.exe .\list.py 'C:\Games\UltraStar WorldParty\songs' 'C:\Games\UltraStar WorldParty\playlists\'
# 
def seconds_to_str(seconds):
    return str(datetime.timedelta(seconds=seconds))

def do_backup(filename, ext="bak"):
    bckfile = "%s.%s" % (filename, ext)
    shutil.copy2(filename, bckfile)

def store_playlist(songs, playlist_dir, name, encoding=ENCODING):

    text = []
    text.append('#Name: %s' % name)
    text.append('#Songs:')
    
    for song in songs:
        text.append("%s : %s" % (song['artist'], song['title']))
      
    filename = os.path.sep.join([playlist_dir, "%s.upl" % name])
    do_backup(filename)
    with open(filename, 'w', encoding=encoding) as f:
        f.write("\n".join(text))

    print("Playlist %s created with %d songs" % (name, len(songs)))


def update_config(filename, field, newvalue, encoding=ENCODING):
    
    new_file = []
    with open(filename,'r', encoding=encoding) as f:
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
    
    do_backup(filename)
    with open(filename, 'w', encoding=encoding) as f:
        f.write("\n".join(new_file))    
    

def update_song_file(song_dirname, field, value):

    path = os.path.dirname(song_dirname)
    entry = os.path.basename(song_dirname)
    
    song_config = "%s" % os.path.sep.join( [ song_dirname, entry ] )
    song_config_multi = "%s [MULTI]" % song_config
    song_config = "%s.txt" % song_config
    song_config_multi = "%s.txt" % song_config_multi

    if os.path.exists(song_config):
        update_config(song_config, field, value)
    
    if os.path.exists(song_config_multi):
        update_config(song_config_multi, field, value)
    


def get_songs(dirname, verbose=False):

    SongInfo = namedtuple('SongInfo', ['config','is_multi', 'dirname' ])
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
            print("Warning: '%s' has no config" % entry)
            continue

        if not os.path.exists(song_config_multi):
            song_config_multi = None

        songs.append( SongInfo(config=song_config,
                               is_multi=song_config_multi,
                               dirname=full_path)
                    )
    return songs

def add_tags(tags, data, fname, encoding=ENCODING):
    
    # is not multi, so go out
    if not fname: 
        return 
    
    for item in tags:
        tag, value = item
        entry = "#%s:%s\n" % (tag.upper(), value)
        data = entry + data
    
    do_backup(fname)
    with open(fname, 'w', encoding=encoding) as f:
        f.write(data)    

def read_config(data, fname):
    """
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
    
    # check for missing tags:

    required_tags = [ 'title', 'artist', 'language', 'edition',
                     'genre', 'year', 'mp3', 'cover', 'video',
                     'videogap', 'bpm', 'gap' ]
    

    for tag in required_tags:
        if not tag in config.keys():
            tag_missing_value = "UNKNOWN"
            if tag in [ 'genre', 'edition', 'language', 'artist', 'title']:
                print("tag %s is missing on file %s" % (tag, fname))
                tags.append( (tag, tag_missing_value) )
            if tag in [ 'videogap', 'gap' ]:
                tag_missing_value = 0
            config[tag] = tag_missing_value
            

    return config, tags

def merge_config(config, config_multi, dirname, path):

    players = {}
    is_multi = 0
    if config_multi:
        for item in config_multi.keys():
            if item.startswith('duetsinger'):
                is_multi = 1
                entry = item.replace('duetsinger','')
                players[entry] = config_multi[item]

    filename_mp3 = os.path.sep.join([dirname,config['mp3']])
    print(filename_mp3)
    
    # add synthetic fields

    config['players'] = players
    config['path'] = path
    config['dirname'] = dirname
    config['duration'] = mutagen.mp3.MP3(filename_mp3).info.length
    config['multi'] = is_multi
    return config


def process_songs(songs, verbose=False):

    data = []

    for song in songs:
        
        text = None
        text_multi = None
        config = None
        config_multi = None

        with open(song.config,'r', encoding=ENCODING) as f:
            text = f.read()
            config, tags = read_config(text, song.config)

        if tags:
            add_tags(tags, text, song.config)

        if song.is_multi:
     
            with open(song.is_multi,'r', encoding=ENCODING) as f:
                text_multi = f.read()
                config_multi,tags = read_config(text_multi, song.is_multi)

                if tags:
                    add_tags(tags, text_multi, song.is_multi)



        config = merge_config(config, config_multi, song.dirname, song.config)       
        data.append(config)
    return data


def create_table(cursor):
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
    for sql_sentence in sql_prologue:
        cursor.execute(sql_sentence)
    
    cursor.execute(sql_songs)
    cursor.execute(sql_multi)
    
    for sql_sentence in sql_epilogue:
        cursor.execute(sql_sentence)
    

def insert_into_db(cursor, item):

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
    print(item)
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
    
def store_in_db(config, dbfile=None, refresh=False, database=None, init=True):
    if not refresh:
        if dbfile:
            db = sqlite3.connect(dbfile)
        else:
            db = sqlite3.connect('file:cachedb?mode=memory&cache=shared')
        db.row_factory = sqlite3.Row 
    else:
        db = database
        db.row_factory = sqlite3.Row 
    
    if init:
        create_table(db.cursor())
        cursor = db.cursor()
        for c in config:
            insert_into_db(cursor, c)
        cursor.close()
        print("%d records inserted in DB" % len(config))
    
    db.commit()
    return db

def test_db(db):
    cursor = db.cursor()
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

def console_exit():
    raise SystemExit


# all this functions use DB as global variable. Proceed with caution

def db_get_input(input):
    """if string, run the query and return the items, but if not, return the array

    Args:
        input (str / list): if str run the query, if list pass it

    Returns:
        list: the items
    """

    if isinstance(input, str):
        return db_get_results(input)
    return input


def db_get_results(query):
    cursor = db.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    rows = list(map(lambda x: dict(x), rows))
    cursor.close()
    return rows

def db_get_fields():
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(songs)");
    rows = cursor.fetchall()
    fields = []
    for i in rows:
        fields.append('%s (%s)' % (i[1], i[2]))
    return fields

def db_set_field(input,field, value):
    
    items = db_get_input(input)

    cursor = db.cursor()
    for i in items:
        cursor.execute("update songs set %s=? where id=?" % field, [value,i['id']])
        # save file
        cursor.execute("select * from songs where id = ?", [i['id']])
        song = cursor.fetchone()
        if not song:
            print("warning, can't update song %s (%s:%s)" % (i['id'], field, value))
            continue
        update_song_file(i['dirname'],field=field, value=value)
    cursor.close()





    
def db_refresh_db():
    # careful with the global variables.
    songs = get_songs(args.songs_dir, args.verbose)
    config = process_songs(songs, args.verbose)
    store_in_db(config, dbfile=args.persistent, refresh=True, database=db)

def db_create_playlist(input, name):
    items = db_get_input(input)
    cursor = db.cursor()
    songs = []
    for i in items:
         cursor.execute("select * from songs where id = ?", [i['id']])
         song = cursor.fetchone()
         songs.append({'artist': song['artist'], 'title': song['title']})
    store_playlist(songs, args.playlist_dir, name)


def load_db(path, verbose, dbfile, init_db):
    
    config = []
    if init_db:
        songs = get_songs(path, verbose)
        config = process_songs(songs, verbose)
        print("initializing db from songs")
    
    db = store_in_db(config, dbfile=dbfile, init=init_db)
    return db





if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--persistent", help="Use a persistent database instead the memory one")
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-k", "--keep_db", help="Uses the stored db data instead loading one", action="store_false")
    parser.add_argument("songs_dir", help="Song directory")
    parser.add_argument("playlist_dir", help="Playlist directory")
    args = parser.parse_args()
    
    db = load_db(args.songs_dir, args.verbose, args.persistent, args.keep_db)
    
    #test_db(db)

    # prepare console and run it with the data.

    my_locals = {}
    my_locals["exit"] = console_exit
    my_locals["db"] = db
    my_locals["get"] = db_get_results
    my_locals["fields"] = db_get_fields
    my_locals["set_field"] = db_set_field
    my_locals["refresh"] = db_refresh_db
    my_locals["create_playlist"] = db_create_playlist
    my_locals["seconds_to_str"] = seconds_to_str
    my_locals['LANGUAGES'] = LANGUAGES
    my_locals['EDITIONS'] = EDITIONS
    my_locals['GENRES'] = GENRES
    
    banner = []
    banner.append("Commands:")

    for i in my_locals.keys():
        banner.append("%s" % i)
    banner = "\n".join(banner)
    try:
        code.InteractiveConsole(locals=my_locals).interact(banner=banner)
    except SystemExit:
        pass
    db.close()

    # get("select id,title from songs where genre='UNKNOWN'")
    # get("select id,title from songs where edition='UNKNOWN'")
    # set_edition(get("select * from songs where edition='UNKNOWN'"),"Sin Edición")
    # set_genre(get("select * from songs where genre='UNKNOWN'"),"Pop")
    # create_playlist("select id from songs where genre='Pop'", "mypop")
    # create_playlist(get("select id from songs where genre='Pop'"), "mypop")