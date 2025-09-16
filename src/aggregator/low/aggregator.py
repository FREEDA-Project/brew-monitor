import requests
from flask import Flask, jsonify
import os

app = Flask(__name__)
DATA_GATHER_INSTANCES = os.getenv('DATA_GATHER_INSTANCES', 'data-gather').split(',')

# Aggregator in LOW mode: fetches the value directly from Data Gather.
@app.route("/aggregator/current", methods=["GET"])
def get_current_data():
    for dg in DATA_GATHER_INSTANCES:
        try:
            response = requests.get(f"http://{dg}:5001/data-gather/avg")
            if response.status_code != 200:
                return jsonify({"error": f"Error retrieving data from {dg}"}), response.status_code
            return jsonify(response.json()), response.status_code
        except Exception as e:
            return jsonify({"error": f"Error retrieving value: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
