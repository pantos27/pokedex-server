from flask import Flask, jsonify
import db

app = Flask(__name__)

@app.route('/icon/<name>')
def get_icon_url(name:str):
    return f"https://img.pokemondb.net/sprites/silver/normal/{name}.png"


@app.route('/')
def hello():
    data = db.get()
    return jsonify(data)


if __name__=='__main__':
    app.run(port=8080)