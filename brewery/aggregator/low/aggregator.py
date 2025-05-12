import requests
from flask import Flask, jsonify

app = Flask(__name__)

#Aggregator in LOW: prende il valore direttamente da Data Gather.
@app.route("/aggregator/current", methods=["GET"])
def get_current_data():

    try:
        response = requests.get("http://data-gather:5001/data-gather/latest")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Errore nel recupero del valore: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
