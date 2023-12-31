from flask import Flask, render_template, abort, jsonify, send_from_directory, request, make_response


from flask_bootstrap import  Bootstrap5
import base64
import urllib
import sys
sys.path.append('..')
from ultrastar.songhelper import UltraStarHelper
from ultrastar.appenv import AppEnv
from ultrastar.helper import Helper



def create_app(config_file):
    app = Flask(__name__)
    Bootstrap5(app)
    # to serve all the files from local, instead of CDN
    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    AppEnv.config(config_file)
    AppEnv.print_config()
 

    app.AppEnv = AppEnv
    app.ultrastar_helper =  UltraStarHelper(AppEnv.config())
    app.ultrastar_helper.load_db()

    @app.template_filter()
    def b64encode(s):
        return base64.b64encode(s.encode('utf-8'))

    @app.template_filter()
    def b64decode(s):
        return base64.b64decode(s).decode()

    @app.template_filter()
    def uuencode(s):
        return urllib.parse.quote_plus(s.encode('utf-8'))

    @app.template_filter()
    def uudecode(s):
        return urllib.parse.unquote(s)

    @app.route("/")
    @app.route("/artists")
    def artists():
        search = request.args.get('search', default = "", type = str)
        cursor = app.ultrastar_helper.db.cursor()
        # using the ID to get the cover is somewhat crap
        # but works (the cover of any of the song)
        if search:
            ## add like string format to ease the search
            search = "%%%s%%" % search
            cursor.execute("select artist, id, count(artist) as songs from songs where artist like ? group by(artist) order by artist;",(search,))
        else:
            cursor.execute("select artist, id, count(artist) as songs from songs group by(artist) order by artist;")
        rows = cursor.fetchall()
        cursor.close()
        artist_list = list(map(lambda x: dict(x),rows))
        return render_template("artists.html", 
                               title="UltraStar Artist List", 
                               items = artist_list,
                               search_action = "/")



    @app.route("/playlists")
    def playlists():
        search = request.args.get('search', default = "", type = str)
       
        # using the ID to get the cover is somewhat crap
        # but works (the cover of any of the song)
        # TODO
        if search:
            ## add like string format to ease the search
            playlist_list = app.ultrastar_helper.get_playlists(filter=search)
        else:
            playlist_list = app.ultrastar_helper.get_playlists()

        return render_template("playlists.html", 
                               title="UltraStar Playlists", 
                               items = playlist_list,
                               search_action = "/playlists")


    @app.route("/playlist")
    def playlist():
        playlist_id_uu = request.args.get('name', default = "", type = str)
        
        
        if not playlist_id_uu:
            abort(403)

        playlist_id = uudecode(playlist_id_uu)
        playlist = app.ultrastar_helper.get_playlist(filename=playlist_id)
        if not playlist:
            abort(403)
        title = "Ultrastar Playlist %s" % playlist.name   
        
        
        return render_template("songs.html", 
                               title=title, 
                               artist=None,
                               search=None,
                               playlist=playlist,
                               search_action = "/songs")


    @app.route("/songs")
    def songs():
        artist_id = request.args.get('artist', default = "", type = str)
        search = request.args.get('search', default = "", type = str)
        title="Ultrastar song list"
        if artist_id:
            artist_id = uudecode(artist_id)
            cursor = app.ultrastar_helper.db.cursor()
            cursor.execute("select artist from songs where artist=?",(artist_id,))
            artist = cursor.fetchone()
            cursor.close()
            artist = dict(artist)
            title = "Ultrastar song list for %s" % artist_id   
        
        
        return render_template("songs.html", 
                               title=title, 
                               artist=uuencode(artist_id), 
                               playlist=None,
                               search=search,
                               search_action = "/songs")
    
    
    @app.route("/data")
    def data():
        artist_id = request.args.get('artist', default = "", type = str)
        playlist_id = request.args.get('playlist', default = "", type = str)
        search = request.args.get('search', default = "", type = str)
        cursor = app.ultrastar_helper.db.cursor()
       
        if playlist_id:
            playlist_id = uudecode(playlist_id)
            playlist = app.ultrastar_helper.get_playlist(filename = playlist_id)
            if not playlist:
                abort(403)
            # read the songs.
            rows = playlist.songs
    
            
        else:

            if not search:
                if artist_id:
                    cursor.execute("select * from songs where artist=? order by title",(artist_id,))
                else:
                    cursor.execute("select * from songs;")
            else:
                ## add like string format to ease the search
                search = "%%%s%%" % search
                if artist_id:
                    cursor.execute("select * from songs where artist=? and title like ? order by title",(artist_id,search))
                else:
                    cursor.execute("select * from songs where title like ?;", (search,))
            
            rows = cursor.fetchall()

        data = []
        for row in rows:
            item = dict(row)
            item['duration'] = Helper.seconds_to_str(item['duration'], trim=True)
            item['multi'] = "Yes" if item['multi'] else "No"
            data.append(item)
        json = jsonify(data=data)
        cursor.close()
        return json
    


    @app.route('/img/cover/<id>')
    
    def serve_img(id):
        # use the id of the song to get the cover
        # but use also the cover for the artist
        cursor = app.ultrastar_helper.db.cursor()
        cursor.execute("select dirname,cover from songs where id=?;",(id,))
        item = cursor.fetchone()
        if not item:
            abort(404)
        response = make_response(send_from_directory(item["dirname"], item["cover"], as_attachment=False))
        response.cache_control.max_age = 300
        return response

    @app.route('/mp3/<id>')
    def serve_mp3(id):
        # use the id of the song to get the cover
        # but use also the cover for the artist
        cursor = app.ultrastar_helper.db.cursor()
        cursor.execute("select dirname,mp3 from songs where id=?;",(id,))
        item = cursor.fetchone()
        if not item:
            abort(404)
        response = make_response(send_from_directory(item["dirname"], item["mp3"], as_attachment=False))
        response.cache_control.max_age = 300
        return response

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("error.html", error="Page not found"), 404


    return app