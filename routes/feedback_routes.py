import os
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

# ================================================================
#  🧩 Load Environment & MongoDB
# ================================================================
load_dotenv()

feedback_bp = Blueprint("feedback_bp", __name__)

MONGODB_URI = os.getenv("MONGODB_URI")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://viadocs.in")

# ✅ MongoDB Connection
client = MongoClient(MONGODB_URI)
db = client["viadocsDB"]
feedback_collection = db["feedbacks"]
users_collection = db["users"]

# ================================================================
#  💬 Feedback Route
# ================================================================
@feedback_bp.route("", methods=["POST", "OPTIONS"])
@cross_origin(origins=[FRONTEND_ORIGIN], supports_credentials=True)
@jwt_required(optional=True)
def feedback():
    """Store feedback with user details (if logged in)."""
    try:
        # ✅ Handle preflight (CORS)
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200

        # ✅ Get incoming data
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()
        rating = data.get("rating", "").strip()

        if not message:
            return jsonify({"error": "Feedback message is required"}), 400

        # ============================================================
        #  🔐 Identify User (via JWT, optional)
        # ============================================================
        user_id = get_jwt_identity()
        name = "Guest User"
        email = "N/A"

        if user_id:
            try:
                # Convert JWT user_id (string) → ObjectId
                user_obj = users_collection.find_one({"_id": ObjectId(user_id)})
                if user_obj:
                    first_name = user_obj.get("first_name") or user_obj.get("firstName", "")
                    last_name = user_obj.get("last_name") or user_obj.get("lastName", "")
                    username = user_obj.get("username", "User")
                    name = f"{first_name} {last_name}".strip() or username
                    email = user_obj.get("email", "N/A")
            except Exception as e:
                print("⚠️ feedback user lookup error:", e)

        # ============================================================
        #  🧾 Prepare Feedback Document
        # ============================================================
        feedback_entry = {
            "name": name,
            "email": email,
            "message": message,
            "rating": rating,
            "createdAt": datetime.utcnow(),
        }

        # ✅ Insert into MongoDB
        feedback_collection.insert_one(feedback_entry)

        print(f"✅ Feedback saved from: {name} ({email})")

        return jsonify({"message": "Feedback submitted successfully!"}), 200

    except Exception as e:
        print("❌ feedback route error:", e)
        return jsonify({"error": "Server error. Please try again later."}), 500
