from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
import urllib.parse

app = Flask(__name__)


mongo_username = os.environ.get("MONGO_USERNAME")
mongo_password = os.environ.get("MONGO_PASSWORD")
# Default to localhost if not set (for local testing)
mongo_host = os.environ.get("MONGO_HOST", "localhost") 
mongo_port = os.environ.get("MONGO_PORT", "27017")
mongo_dbname = "flask_db"


if mongo_username and mongo_password:
    # Escape special characters in password just in case 
    username = urllib.parse.quote_plus(mongo_username)
    password = urllib.parse.quote_plus(mongo_password)
    # Standard Connection String for Auth
    mongo_uri = f"mongodb://{username}:{password}@{mongo_host}:{mongo_port}/?authSource=admin"
else:
    # Fallback for simple local testing without auth 
    mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/"

print(f"Connecting to MongoDB at: {mongo_host}:{mongo_port} (Auth: {'Yes' if mongo_username else 'No'})")

client = MongoClient(mongo_uri)
db = client[mongo_dbname]
collection = db.data



@app.route('/')
def index():
    return f"Welcome to the Flask app! The current time is: {datetime.now()}"

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST':
        data_payload = request.get_json()
        collection.insert_one(data_payload)
        return jsonify({"status": "Data inserted"}), 201
    
    elif request.method == 'GET':
        # Exclude _id from result to avoid JSON serialization issues
        data_list = list(collection.find({}, {"_id": 0}))
        return jsonify(data_list), 200

if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5001)