import time
import numpy as np
from flask import Flask, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)


#db MongoDB
client = MongoClient("mongodb://mongodb_history:27017/")
history = client.history
history_db = history.sensor_history

#Recupera i dati delle ultime 24 ore dal database History.
def get_last_24_hours():
    cutoff_time = time.time() - 86400  # Timestamp 24h fa in formato stringa
    return list(history_db.find({"timestamp": {"$gte": cutoff_time}}))
 
 
def format_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

#Genera statistiche sui dati delle ultime 24 ore.
@app.route("/analyzer/stats", methods=["GET"])
def analyze_data():
    data_list = get_last_24_hours()

    if not data_list:
        return jsonify({"error": "Nessun dato disponibile per le ultime 24 ore"}), 404

    for entry in data_list:
        entry.pop("_id", None)  
        entry["timestamp"] = format_timestamp(entry["timestamp"])
    
    temperatures = [d["avg_temperature"] for d in data_list if "avg_temperature" in d]
    humidities = [d["avg_humidity"] for d in data_list if "avg_humidity" in d]
    ph_values = [d["avg_ph"] for d in data_list if "avg_ph" in d]

    if not temperatures or not humidities or not ph_values:
        return jsonify({"error": "Dati insufficienti per calcolare statistiche"}), 400

    stats = {
        "temperature": {
            "max": max(temperatures),
            "min": min(temperatures),
            "dev_std": round(np.std(temperatures), 3), 
            "outliers": [t for t in temperatures if t < 18 or t > 22]
        },
        "humidity": {
            "max": max(humidities),
            "min": min(humidities),
            "dev_std": round(np.std(humidities), 3)
        },
        "ph": {
            "max": max(ph_values),
            "min": min(ph_values),
            "dev_std": round(np.std(ph_values), 3),
            "outliers": [p for p in ph_values if p < 5 or p > 7]
        }
    }

    return jsonify(stats), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
