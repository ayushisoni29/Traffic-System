from flask import Flask, jsonify

app = Flask(__name__)
state = {"signal": "N", "last_update": "none"}

@app.route("/status")
def status():
    return jsonify(state)

@app.route("/change/<direction>")
def change(direction):
    state["signal"] = direction
    return jsonify(state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
