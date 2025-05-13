import time
import requests
from flask import Flask, jsonify
from threading import Thread
from datetime import datetime
from pymongo import MongoClient


def format_timestamp(ts):
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

#db MongoDB
app = Flask(__name__)
client = MongoClient("mongodb://mongodb_history:27017/")
history = client.history
history_db = history.sensor_history

def periodic_data_gathering():
    while True:
        try:
            # Chiamata al Data Gather per ottenere la media dei dati più recenti
            response = requests.get("http://data-gather:5001/data-gather/avg")

            if response.status_code == 200:
                avg_data = response.json()
                avg_data["timestamp"] = time.time() 
                history_db.insert_one(avg_data)  
                print(f"[Aggregator] Dati salvati nel database History: {avg_data}")
            else:
                print(f"[Aggregator] Errore nella richiesta al Data Gather: {response.status_code}")

        except Exception as e:
            print(f"Errore nell'Aggregator: {e}")

        time.sleep(60) 

#Ottiene l'ultimo valore salvato nel database History
@app.route("/aggregator/current", methods=["GET"])
def get_current_data():
    try:
        last_entry = history_db.find_one({}, sort=[("timestamp", -1)])
        
        if not last_entry:
            return jsonify({"error": "Nessun dato disponibile"}), 404
        
        last_entry.pop("_id", None)
        last_entry["timestamp"] = format_timestamp(last_entry["timestamp"])

        return jsonify(last_entry), 200
            
    except Exception as e:
        return jsonify({"error": f"Errore interno aggregator: {e}"}), 500

if __name__ == "__main__":
    Thread(target=periodic_data_gathering).start()
    app.run(host="0.0.0.0", port=5002)
