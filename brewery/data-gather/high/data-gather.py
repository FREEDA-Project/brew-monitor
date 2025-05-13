import time
import random
from flask import Flask, jsonify
from pymongo import MongoClient

# Collezioni specifiche
app = Flask(__name__)

client = MongoClient("mongodb://mongodb_batch:27017/")
client.admin.command('ping')  
print("Connesso a MongoDB!")

# Collezioni specifiche per i vari servizi
batch_db = client.batch_db
batch_collection=batch_db.sensor_data  # Batch per il Data Gather

# TTL per dati più vecchi di 24 ore
batch_collection.create_index([("timestamp", 1)], expireAfterSeconds=86400)

# Variabile globale per tracciare il timestamp dell'ultima chiamata
last_call_time = time.time()


# Genera dati ogni secondo e li salva nel database Batch
def generate_data():
    while True:
        data = {
            "humidity": random.uniform(40, 60),
            "temperature": random.uniform(10, 30),
            "ph": random.uniform(5, 7),
            "timestamp": time.time()
        }
        batch_collection.insert_one(data)
        print(f"Dato generato: {data}",flush=True)
        time.sleep(1)

# API per ottenere la media dei dati più recenti
@app.route('/data-gather/avg', methods=['GET'])
def get_avg_data():
    global last_call_time

    # dati generati dopo `last_call_time`
    recent_data = batch_collection.find({"timestamp": {"$gte": last_call_time}})
   
    last_call_time = time.time()
    data_list = list(recent_data)

    if not data_list:
        return jsonify({"error": "Nessun dato disponibile"}), 404

    avg_humidity = sum(d["humidity"] for d in data_list) / len(data_list)
    avg_temperature = sum(d["temperature"] for d in data_list) / len(data_list)
    avg_ph = sum(d["ph"] for d in data_list) / len(data_list)

   
    return jsonify({
        "avg_humidity": avg_humidity,
        "avg_temperature": avg_temperature,
        "avg_ph": avg_ph
    }), 200

if __name__ == "__main__":
    from threading import Thread
    Thread(target=generate_data).start()
    app.run(host="0.0.0.0", port=5001)
