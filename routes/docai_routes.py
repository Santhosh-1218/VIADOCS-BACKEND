import os
from flask import Blueprint, request, jsonify
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import cross_origin

# Load .env
load_dotenv()

docai_bp = Blueprint("docai_bp", __name__)

# Environment values
MONGODB_URI = os.getenv("MONGODB_URI")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client["viadocsDB"]
docai_collection = db["docai_requests"]

# ✅ FIXED ROUTE (no duplicate prefix)
@docai_bp.route("/early-access", methods=["POST", "OPTIONS"])
@cross_origin(origins=[FRONTEND_ORIGIN])
def early_access():
    # Handle browser preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True)
    email = data.get("email") if data else None

    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Prevent duplicate submissions
    existing = docai_collection.find_one({"email": email})
    if existing:
        return jsonify({"message": "Email already registered for early access"}), 200

    # Save new entry
    docai_collection.insert_one({
        "email": email,
        "createdAt": datetime.utcnow()
    })

    return jsonify({"message": "Early access request saved successfully"}), 200
