from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
import os

user_bp = Blueprint("user_bp", __name__)

# ---------------------- GET PROFILE ----------------------
@user_bp.route("/profile", methods=["GET", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def get_profile():
    """Fetch user profile details"""
    db = current_app.db
    user_id = get_jwt_identity()

    user = db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id": str(user["_id"]),
        "username": user.get("username", ""),
        "firstName": user.get("first_name", ""),
        "lastName": user.get("last_name", ""),
        "fullName": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
        "email": user.get("email", ""),
        "dateOfBirth": user.get("dob", ""),
        "gender": user.get("gender", ""),
        "role": user.get("role", ""),
        "premium": user.get("premium", False),
        "profileImage": user.get("profile_image", None)
    }), 200


# ---------------------- UPDATE PROFILE ----------------------
@user_bp.route("/profile", methods=["PUT", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def update_profile():
    """Update profile fields (name, DOB, etc.)"""
    db = current_app.db
    user_id = get_jwt_identity()
    data = request.get_json()
    update_fields = {}

    if "firstName" in data:
        update_fields["first_name"] = data["firstName"]
    if "lastName" in data:
        update_fields["last_name"] = data["lastName"]
    if "dateOfBirth" in data:
        update_fields["dob"] = data["dateOfBirth"]

    if not update_fields:
        return jsonify({"message": "No valid fields to update"}), 400

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    user = db.users.find_one({"_id": ObjectId(user_id)})

    return jsonify({
        "id": str(user["_id"]),
        "firstName": user.get("first_name", ""),
        "lastName": user.get("last_name", ""),
        "dateOfBirth": user.get("dob", ""),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "profileImage": user.get("profile_image", None),
    }), 200


# ---------------------- UPLOAD PROFILE IMAGE ----------------------
@user_bp.route("/profile/upload", methods=["PUT", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def upload_profile_image():
    """Upload and save profile picture to /uploads/profile_images"""
    db = current_app.db
    user_id = get_jwt_identity()

    if "profileImage" not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files["profileImage"]
    if file.filename == "":
        return jsonify({"message": "Empty filename"}), 400

    # ✅ Save to uploads/profile_images folder
    uploads_dir = os.path.join(current_app.root_path, "uploads", "profile_images")
    os.makedirs(uploads_dir, exist_ok=True)

    filename = f"profile_{user_id}_{int(datetime.utcnow().timestamp())}.jpg"
    file_path = os.path.join(uploads_dir, filename)
    file.save(file_path)

    image_url = f"/uploads/profile_images/{filename}"

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_image": image_url}}
    )

    return jsonify({
        "message": "Profile image updated successfully",
        "profileImage": image_url
    }), 200


# ---------------------- SET USER ROLE ----------------------
@user_bp.route("/profile/role", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def set_role():
    """Save user type (Student / Employee)"""
    db = current_app.db
    user_id = get_jwt_identity()
    data = request.get_json()
    role = data.get("role")

    if role not in ["student", "employee"]:
        return jsonify({"error": "Invalid role"}), 400

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": role}})
    return jsonify({"message": "Role saved successfully", "role": role}), 200
