# backend/routes/user_activity_routes.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from bson import ObjectId

activity_bp = Blueprint("activity_bp", __name__)

@activity_bp.route("/track-usage", methods=["POST"])
@jwt_required()
def track_usage():
    """
    Logs user's daily usage time (minutes).
    Skips if admin or invalid ObjectId.
    """
    try:
        db = current_app.db
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        duration = float(data.get("duration", 0))

        # ✅ Skip invalid or admin users
        if not user_id or user_id.lower() == "admin":
            print("ℹ️ Skipping activity tracking for admin user.")
            return jsonify({"message": "Admin activity not tracked."}), 200

        # ✅ Check valid ObjectId
        if not ObjectId.is_valid(user_id):
            print(f"❌ Invalid ObjectId for user: {user_id}")
            return jsonify({"error": "Invalid user ID"}), 400

        if not duration or duration <= 0:
            return jsonify({"error": "Invalid duration"}), 400

        today = datetime.utcnow().strftime("%Y-%m-%d")
        user_activity_col = db["user_activity"]

        existing_entry = user_activity_col.find_one({
            "user_id": ObjectId(user_id),
            "date": today
        })

        if existing_entry:
            user_activity_col.update_one(
                {"_id": existing_entry["_id"]},
                {
                    "$set": {"updated_at": datetime.utcnow()},
                    "$inc": {"total_minutes": duration}
                }
            )
        else:
            user_activity_col.insert_one({
                "user_id": ObjectId(user_id),
                "date": today,
                "total_minutes": duration,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

        return jsonify({"message": "Usage time recorded successfully"}), 200

    except Exception as e:
        print("❌ track_usage error:", e)
        return jsonify({"error": str(e)}), 500
