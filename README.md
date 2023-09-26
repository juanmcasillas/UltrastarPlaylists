# UltrastarPlaylists
Manage &amp; Create playlist and sort the song database from Ultrastar with sql and a interactive shell, in python

## Motivation
Create easily and fast playlist, based on sql queries using all the data fields in the songs, also, support for changing some attributes in the songs, and detect if the song has duets and son on. The code is a work in progress, but it pretty functional


## Dependencies

 * python
 * C:\software\python311\python.exe -m pip install Flask==2.3.3
 * C:\software\python311\python.exe -m pip install flask-bootstrap
 * C:\software\python311\python.exe -m pip install mutagen 


## Run
 * `C:\software\python311\Scripts\flask.exe --app .\app.py run`
 * `flask.exe --app app run --debug`
 
http://127.0.0.1:5000/


## Commands

`python.exe .\list.py 'C:\Games\UltraStar WorldParty\songs' 'C:\Games\UltraStar WorldParty\playlists'` Launch the script with 
the song directory and playlist directory. Normally `songs` and `playlists`. On the interactive shell, we have the following
commands:

* `exit` function. Exist from shell (also ^Z)
* `get` function. Executes a query and return a python array of dicts
* `fields` function. Return the fields of the table `songs`
* `set_genre` function. Set a given collection a given genre `id` must be present. Updates the song files.
* `set_edition` function. Set a given collection a given edition `id` must be present. Updates the song files.
* `refresh` function. Refresh the DB from the song configuration files
* `create_playlist` function. Create a playlist with the given collection.
* `db` variable. the song database.
* `LANGUAGES` variable. All the available languages, in a dict (en, es)
* `EDITIONS` variable. All the Singstar editions.
* `GENRES` variable. All the genres.

## Examples

* `get("select id,title from songs where genre='UNKNOWN'")` Get all the songs that have genre = 'UNKNOWN'
* `get("select id,title from songs where edition='UNKNOWN'")` The same, with edition
* `set_edition(get("select * from songs where edition='UNKNOWN'"),"Sin Edición")` Change all the songs without edition to 'Sin Edición'
* `set_genre(get("select * from songs where genre='UNKNOWN'"),"Pop")` Set all unknown genre to 'Pop'
* `create_playlist(get("select id from songs where genre='Pop'"), "mypop")` Create a playlist called mypop, using all the songs in genre Pop
* ` get("select id, title from songs where language in ( 'Español', 'Spanish' ) and genre = 'Pop' ")` Get songs in spanish and genre pop

