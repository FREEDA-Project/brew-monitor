import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Indirizzi dei servizi sottostanti
ANALYZER_URL = "http://analyzer:5003/analyzer/stats"
AGGREGATOR_URL = "http://aggregator:5002/aggregator/current"

@app.route("/api/analyzer/stats", methods=["GET"])
def get_analyzer_stats():
    try:
        response = requests.get(ANALYZER_URL)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Analyzer non disponibile: {str(e)}"}), 500

@app.route("/api/aggregator/current", methods=["GET"])
def get_aggregator_data():
    try:
        response = requests.get(AGGREGATOR_URL)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Aggregator non disponibile: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
