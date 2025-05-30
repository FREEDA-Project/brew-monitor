
from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os
from pymongo import MongoClient
import threading
import time

app = Flask(__name__)

# Configurazione MongoDB
client = MongoClient('mongodb://mongodb-history:27017')
db = client['history']  # Seleziona il database 'history'
DATA_GATHER_INSTANCES = os.getenv('DATA_GATHER_INSTANCES', 'data-gather').split(',')

# Funzione per ottenere l'ultima entry di una collezione

def periodic_data_gathering():
    while True:
        for dg in DATA_GATHER_INSTANCES:
            try:
                # Chiama il data-gather specifico
                response = requests.get(f'http://{dg}:5001/data-gather/avg')
                if response.status_code == 200:
                    data = response.json()
                    
                    # Salva i dati nella collezione specifica per questo data-gather
                    collection = db[dg]  
                    data['timestamp'] = datetime.now()
                    collection.insert_one(data)
                    print(f"Data gathered from {dg}")
                else:
                    print(f"Error from {dg}: status {response.status_code}")
            except Exception as e:
                print(f"Error gathering data from {dg}: {str(e)}")
        
        time.sleep(60) 



@app.route('/aggregator/current', methods=['GET'])
def get_current_data():
    
    results = {}
    
    for dg in DATA_GATHER_INSTANCES:
        try:
            collection = db[dg]  
            latest_data = collection.find_one(sort=[('timestamp', -1)])
            if latest_data:
                latest_data.pop('_id', None)
                results[dg] = latest_data
            else:
                return jsonify({"error": f"Nessun dato disponibile per {dg}"}), 404
        
        except Exception as e:
            return jsonify({"error": f"Errore interno aggregator: {e}"}), 500
    
    return jsonify(results), 200

if __name__ == '__main__':
    # Avvia il thread per la raccolta periodica dei dati
    data_gathering_thread = threading.Thread(target=periodic_data_gathering)
    data_gathering_thread.daemon = True
    data_gathering_thread.start()
    
    # Avvia il server Flask
    app.run(host='0.0.0.0', port=5002) 
