from flask import Flask, jsonify

__version__ = "0.0.1"

app = Flask(__name__)


@app.get("/version")
def version():
    return jsonify({"version": __version__})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
