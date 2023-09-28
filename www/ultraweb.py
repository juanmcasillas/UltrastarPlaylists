from flask import Flask, render_template, abort, jsonify, send_from_directory
from flask_bootstrap import  Bootstrap5


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
    @app.route("/")
    def main():
        return render_template("artists.html", title="UltraStar Artist List")


    @app.route("/tdemo")
    def tdemo():
        return render_template("tdemo.html", title="UltraStar table demo")


    @app.route("/data")
    def data():

        cursor = app.ultrastar_helper.db.cursor()
        cursor.execute("select * from songs;")
        rows = cursor.fetchall()

        data = []
        for row in rows:
            item = dict(row)
            item['duration'] = Helper.seconds_to_str(item['duration'], trim=True)
            item['multi'] = "Yes" if item['multi'] else "No"
            data.append(item)
        json = jsonify(data=data)
        print(json)
        cursor.close()
        return json

    @app.route('/img/cover/<id>')
    def download_file(id):

        cursor = app.ultrastar_helper.db.cursor()
        cursor.execute("select dirname,cover from songs where id=?;",id)
        item = cursor.fetchone()
        if not item:
            abort(404)

        return send_from_directory(item["dirname"], item["cover"], as_attachment=False)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("error.html", error="Page not found"), 404


    return app