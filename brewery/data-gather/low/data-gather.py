import time
import random
from flask import Flask, jsonify

app = Flask(__name__)
latest_value = None

def generate_data():
    global latest_value
    while True:
        latest_value = {
            "temperature": round(random.uniform(15, 25), 2),
            "humidity": round(random.uniform(40, 60), 2),
            "ph": round(random.uniform(5, 7), 2),
            "timestamp": time.time()
        }
        time.sleep(1)  # Genera un nuovo valore ogni secondo

#Restituisce solo l'ultimo valore generato.
@app.route("/data-gather/latest", methods=["GET"])
def get_latest_value():
    
    if latest_value is None:
        return jsonify({"error": "Nessun valore generato ancora"}), 404
    return jsonify(latest_value), 200

if __name__ == "__main__":
    from threading import Thread
    Thread(target=generate_data).start()
    app.run(host="0.0.0.0", port=5001)
