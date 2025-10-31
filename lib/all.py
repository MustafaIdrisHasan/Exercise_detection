from flask import Flask, jsonify
from threading import Thread
import lateral_raises
import shoulder
import crunches
import bicep
import combine

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Exercise Detection API"})

@app.route('/lateral_raises', methods=['POST'])
def lateral_raises_endpoint():
    try:
        Thread(target=lateral_raises.lateral_raises).start()
        return jsonify({"status": "Lateral Raises Detection started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/shoulder_press', methods=['POST'])
def shoulder_press_endpoint():
    try:
        Thread(target=shoulder.shoulder_press).start()
        return jsonify({"status": "Shoulder Press Detection started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/crunches', methods=['POST'])
def crunches_endpoint():
    try:
        Thread(target=crunches.crunches).start()
        return jsonify({"status": "Crunches Detection started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/bicep_curls', methods=['POST'])
def bicep_curls_endpoint():
    try:
        Thread(target=bicep.bicep_curl_detection).start()
        return jsonify({"status": "Bicep Curl Detection started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
