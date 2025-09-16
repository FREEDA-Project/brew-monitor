import random
import time
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Returns the latest generated value
@app.route("/data-gather/avg", methods=["GET"])
def get_latest_value():
    latest_value = {
        "temperature": round(random.uniform(10, 30), 2),
        "humidity": round(random.uniform(40, 60), 2),
        "ph": round(random.uniform(5, 7), 2),
        "timestamp": datetime.now()
    }
    return jsonify(latest_value), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
