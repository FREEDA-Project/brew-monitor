from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os
from pymongo import MongoClient
import threading
import time

app = Flask(__name__)

# MongoDB Configuration
client = MongoClient('mongodb://mongodb-history:27017')
db = client['history']  # Select the 'history' database
DATA_GATHER_INSTANCES = os.getenv('DATA_GATHER_INSTANCES', 'data-gather').split(',')

# Periodic data gathering function
def periodic_data_gathering():
    while True:
        for dg in DATA_GATHER_INSTANCES:
            try:
                # Call the specific data-gather instance
                response = requests.get(f'http://{dg}:5001/data-gather/avg')
                if response.status_code == 200:
                    data = response.json()
                    
                    # Save the data in the specific collection for this data-gather
                    collection = db[dg]  
                    data['timestamp'] = datetime.now()
                    collection.insert_one(data)
                    print(f"Data gathered from {dg}")
                else:
                    print(f"Error from {dg}: status {response.status_code}")
            except Exception as e:
                print(f"Error gathering data from {dg}: {str(e)}")
        
        time.sleep(60)  # Wait 1 minute before the next collection cycle


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
                return jsonify({"error": f"No data available for {dg}"}), 404
        
        except Exception as e:
            return jsonify({"error": f"Internal aggregator error: {e}"}), 500
    
    return jsonify(results), 200


if __name__ == '__main__':
    # Start the thread for periodic data gathering
    data_gathering_thread = threading.Thread(target=periodic_data_gathering)
    data_gathering_thread.daemon = True
    data_gathering_thread.start()
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=5002)
