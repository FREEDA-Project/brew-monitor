from flask import Flask, jsonify
from datetime import datetime, timedelta
from pymongo import MongoClient
import csv
import time
import numpy as np
import os
app = Flask(__name__)

# Configurazione MongoDB
client = MongoClient('mongodb://mongodb-history:27017')
db = client['history']
DATA_GATHER_INSTANCES = os.getenv('DATA_GATHER_INSTANCES', 'data-gather').split(',')



@app.route('/analyzer/stats', methods=['GET'])
def analyze_data():
    
    results = {}
    
    for dg in DATA_GATHER_INSTANCES:
        try:
            # Ottieni l'ultima entry per questo data-gather
            collection = db[dg]
            cutoff_time = datetime.utcnow() - timedelta(days=1)

            
            latest_data = list(collection.find({"timestamp": {"$gte": cutoff_time}}))
            
            if not latest_data:
                return jsonify({"error": f"Nessun dato disponibile per le ultime 24 ore in {dg}"}), 404
            
            for entry in latest_data:
                entry.pop("_id", None)  
                

            temperatures = [d["temperature"] for d in latest_data if "temperature" in d]
            humidities = [d["humidity"] for d in latest_data if "humidity" in d]
            ph_values = [d["ph"] for d in latest_data if "ph" in d]

            if not temperatures or not humidities or not ph_values:
                return jsonify({"error": "Dati insufficienti per calcolare statistiche"}), 400

                # Analisi per area specifica
            area_analysis = {
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
            results[dg] = area_analysis
        
        except Exception as e:
            return jsonify({"error": f"Errore interno analyzer: {str(e)}"}), 500
    
    return jsonify(results),200,{'Content-Type': 'application/json', 'Indent': '4'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003) 
