from flask import Flask, render_template, abort, jsonify
from flask_bootstrap import Bootstrap

def create_app():
  app = Flask(__name__)
  Bootstrap(app)
  return app


app = create_app()

@app.route("/")
def main():
     return render_template("main.html", title="UltraStar song List")


@app.route("/tdemo")
def tdemo():
     return render_template("tdemo.html", title="UltraStar table demo")


@app.route("/data")
def data():
    
    d = [
        {'id': 1, 'artist': 'artist 1', 'song': 'song 1' },
        {'id': 2, 'artist': 'artist 2', 'song': 'song 2' },
    ]

    return jsonify(data=d)



@app.errorhandler(404)
def page_not_found(error):
    return render_template("error.html", error="Page not found"), 404

