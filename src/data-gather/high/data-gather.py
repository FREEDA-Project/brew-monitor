from flask import Flask, jsonify
import random
import time
from datetime import datetime
import os
from pymongo import MongoClient
from threading import Thread

app = Flask(__name__)

# Get instance name from environment
INSTANCE_NAME = os.getenv('INSTANCE_NAME', '')
DB_NAME = f"-{INSTANCE_NAME}"
COLLECTION_NAME = f"{INSTANCE_NAME}"
print(f"MongoDB collection: {COLLECTION_NAME}")

# Connect to MongoDB
client = MongoClient(f'mongodb://mongodb-batch{DB_NAME}:27017')
db = client['brewery']
collection = db[COLLECTION_NAME]

# TTL: remove data older than 24 hours
collection.create_index([("timestamp", 1)], expireAfterSeconds=86400)

# Global variable to track the timestamp of the last call
last_call_time = datetime.now()


def generate_data():
    """Background thread that generates random sensor data."""
    while True:
        data = {
            "timestamp": datetime.now(),
            "temperature": round(random.uniform(10, 30), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "ph": round(random.uniform(5, 7), 2)
        }
        collection.insert_one(data)
        time.sleep(1)


@app.route('/data-gather/avg', methods=['GET'])
def get_data():
    """Return the average values since the last request."""
    global last_call_time

    # Query data since the last request
    data = collection.find({"timestamp": {"$gte": last_call_time}})
    last_call_time = datetime.now()

    data_list = list(data)
    if not data_list:
        return jsonify({"error": "No data available"}), 404

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
    # Start background data generation
    Thread(target=generate_data, daemon=True).start()
    app.run(host="0.0.0.0", port=5001)
