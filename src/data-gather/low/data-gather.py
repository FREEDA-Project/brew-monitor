import time
import random
from flask import Flask, jsonify
from datetime import datetime
app = Flask(__name__)

#Restituisce  l'ultimo valore generato.
@app.route("/data-gather/avg", methods=["GET"])
def get_latest_value():
    latest_value = {
            "temperature": round(random.uniform(10, 30), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "ph": round(random.uniform(5, 7), 2),
            "timestamp": datetime.now()
        }
    if latest_value is None:
        return jsonify({"error": "Nessun valore generato ancora"}), 404
    return jsonify(latest_value), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
