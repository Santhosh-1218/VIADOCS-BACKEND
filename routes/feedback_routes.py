import os
from flask import Blueprint, request, jsonify
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

# Load environment variables
load_dotenv()

feedback_bp = Blueprint("feedback_bp", __name__)

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://viadocs.in")

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client["viadocsDB"]
feedback_collection = db["feedbacks"]
users_collection = db["users"]

# ✅ Feedback Route (Stores Name, Email, Message, Rating)
@feedback_bp.route("", methods=["POST", "OPTIONS"])
@cross_origin(origins=[FRONTEND_ORIGIN], supports_credentials=True)
@jwt_required(optional=True)
def feedback():
    """Collect feedback and store user details (if logged in)."""
    # Handle preflight (CORS)
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # Extract incoming data
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    rating = data.get("rating")

    if not message:
        return jsonify({"error": "Feedback message is required"}), 400

    # 🔐 Identify user (optional JWT)
    user_id = get_jwt_identity()
    name = "Guest User"
    email = "N/A"

    if user_id:
        try:
            # Convert string ID → ObjectId safely
            user_obj = users_collection.find_one({"_id": ObjectId(user_id)})
            if user_obj:
                first_name = user_obj.get("first_name") or user_obj.get("firstName", "")
                last_name = user_obj.get("last_name") or user_obj.get("lastName", "")
                username = user_obj.get("username", "User")
                name = f"{first_name} {last_name}".strip() or username
                email = user_obj.get("email", "N/A")
        except Exception as e:
            print("⚠️ feedback user lookup error:", e)

    # Create feedback document
    feedback_entry = {
        "name": name,
        "email": email,
        "message": message.strip(),
        "rating": rating,
        "createdAt": datetime.utcnow(),
    }

    # Insert into MongoDB Atlas
    feedback_collection.insert_one(feedback_entry)
    print(f"✅ Feedback saved: {name} ({email})")

    return jsonify({"message": "Feedback submitted successfully!"}), 200
