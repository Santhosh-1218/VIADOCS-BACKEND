import os
from flask import Blueprint, request, jsonify
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

# Load environment variables
load_dotenv()

feedback_bp = Blueprint("feedback_bp", __name__)

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client["viadocsDB"]
feedback_collection = db["feedbacks"]
users_collection = db["users"]

# ✅ Correct route (NO /api/feedback inside)
@feedback_bp.route("", methods=["POST", "OPTIONS"])
@cross_origin(origins=[FRONTEND_ORIGIN])
@jwt_required(optional=True)
def feedback():
    # Handle preflight request (CORS)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True)
    message = data.get("message") if data else None
    rating = data.get("rating") if data else None

    if not message:
        return jsonify({"error": "Feedback message is required"}), 400

    # 🔐 Try to identify user via JWT
    user_id = get_jwt_identity()
    name = "Guest User"
    email = "N/A"

    if user_id:
        user_info = users_collection.find_one({"_id": user_id})
        if user_info:
            name = f"{user_info.get('firstName', '')} {user_info.get('lastName', '')}".strip() or user_info.get("username", "User")
            email = user_info.get("email", "N/A")

    feedback_entry = {
        "name": name,
        "email": email,
        "message": message.strip(),
        "rating": rating,
        "createdAt": datetime.utcnow(),
    }

    feedback_collection.insert_one(feedback_entry)

    return jsonify({"message": "Feedback submitted successfully!"}), 200
