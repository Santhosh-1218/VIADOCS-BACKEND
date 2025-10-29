import os
from flask import Blueprint, request, jsonify
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import cross_origin

# Load environment variables
load_dotenv()

contact_bp = Blueprint("contact_bp", __name__)

# Get environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# Connect to MongoDB Atlas
client = MongoClient(MONGODB_URI)
db = client["viadocsDB"]
contact_collection = db["contact_messages"]
@contact_bp.route("", methods=["POST", "OPTIONS"])
@cross_origin(origins=[FRONTEND_ORIGIN])
def contact():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True)
    name = data.get("name") if data else None
    email = data.get("email") if data else None
    message = data.get("message") if data else None

    if not name or not email or not message:
        return jsonify({"error": "All fields are required"}), 400

    new_message = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "message": message.strip(),
        "createdAt": datetime.utcnow(),
    }

    contact_collection.insert_one(new_message)
    return jsonify({"message": "Contact message saved successfully"}), 200
