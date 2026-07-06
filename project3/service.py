from flask import Flask, request, jsonify

app = Flask(__name__)

state = {
    "mode": "auto",   # default mode = automatic
    "signals": {
        "North": "Red",
        "South": "Red",
        "East": "Red",
        "West": "Red"
    },
    "vehicle_count": {}
}

@app.route("/update_signal", methods=["POST"])
def update_signal():
    data = request.get_json()
    lane = data.get("lane")
    signal = data.get("signal")
    
    if lane and signal:
        state["signals"][lane] = signal
        state["mode"] = "manual"  # switch to manual override
        return jsonify({"status": "success", "mode": "manual", "signals": state["signals"]})
    return jsonify({"status": "error"}), 400

@app.route("/switch_auto", methods=["POST"])
def switch_auto():
    state["mode"] = "auto"
    return jsonify({"status": "success", "mode": "auto"})

@app.route("/update_vehicle_count", methods=["POST"])
def update_vehicle_count():
    data = request.get_json()
    lane = data.get("lane")
    count = data.get("count")

    if lane and count is not None:
        state["vehicle_count"][lane] = count
        # Agar auto mode hai to yahan pe signal update karne ka logic add karenge
        if state["mode"] == "auto":
            # Example: jis lane pe sabse zyada gaadi usko green kar do
            max_lane = max(state["vehicle_count"], key=state["vehicle_count"].get)
            for l in state["signals"]:
                state["signals"][l] = "Red"
            state["signals"][max_lane] = "Green"
        return jsonify({"status": "success", "state": state})
    return jsonify({"status": "error"}), 400

@app.route("/get_state", methods=["GET"])
def get_state():
    return jsonify(state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
