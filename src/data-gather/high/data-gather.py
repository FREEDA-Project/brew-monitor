from flask import Flask, jsonify
import random
import time
from datetime import datetime
import os
from pymongo import MongoClient

app = Flask(__name__)

# Ottieni il nome dell'istanza dall'ambiente
INSTANCE_NAME = os.getenv('INSTANCE_NAME', '')
DB_NAME = f"-{INSTANCE_NAME}"
COLLECTION_NAME = f"{INSTANCE_NAME}"
print(f"Collezione MongoDB: {COLLECTION_NAME}")
# Connessione a MongoDB

client = MongoClient(f'mongodb://mongodb-batch{DB_NAME}:27017')
db = client['brewery']
collection = db[COLLECTION_NAME]

# TTL per dati più vecchi di 24 ore
collection.create_index([("timestamp", 1)], expireAfterSeconds=86400)

#Variabile globale per tracciare il timestamp dell'ultima chiamata
last_call_time = datetime.now()

def generate_data():
    while True:
        # Genera dati casuali
        data = {
            'timestamp': datetime.now(),
            "temperature": round(random.uniform(10, 30), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "ph": round(random.uniform(5, 7), 2)
        }
        # Inserisci i dati nella collezione specifica
        collection.insert_one(data)
        time.sleep(1)

@app.route('/data-gather/avg', methods=['GET'])
def get_data():
    global last_call_time
   
    data = collection.find({"timestamp": {"$gte": last_call_time}})
    
    last_call_time = datetime.now()

    data_list = list(data)

    if not data_list:
        return jsonify({"error": "Nessun dato disponibile"}), 404

    avg_humidity = sum(d["humidity"] for d in data_list) / len(data_list)
    avg_temperature = sum(d["temperature"] for d in data_list) / len(data_list)
    avg_ph = sum(d["ph"] for d in data_list) / len(data_list)

   
    return jsonify({
        "humidity": avg_humidity,
        "temperature": avg_temperature,
        "ph": avg_ph,
        "timestamp": datetime.now()
    }), 200


if __name__ == "__main__":
    from threading import Thread
    Thread(target=generate_data,daemon=True).start()
    app.run(host="0.0.0.0", port=5001)
