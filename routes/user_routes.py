from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
import uuid

user_bp = Blueprint("user_bp", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------- GET PROFILE ----------------------
@user_bp.route("/profile", methods=["GET", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def get_profile():
    """Fetch user profile details"""
    db = current_app.db
    user_id = get_jwt_identity()

    user = db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Convert stored Base64 image to usable data URI
    profile_image_url = None
    if user.get("profile_image"):
        if user["profile_image"].startswith("data:image/"):
            profile_image_url = user["profile_image"]
        else:
            # In case legacy URLs exist
            profile_image_url = user["profile_image"]

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
        "profileImage": profile_image_url,
    }), 200


# ---------------------- UPDATE PROFILE ----------------------
@user_bp.route("/profile", methods=["PUT", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def update_profile():
    """Update profile fields (name, DOB, etc.)"""
    db = current_app.db
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    update_fields = {}

    if "firstName" in data:
        update_fields["first_name"] = data["firstName"]
    if "lastName" in data:
        update_fields["last_name"] = data["lastName"]
    if "dateOfBirth" in data:
        update_fields["dob"] = data["dateOfBirth"]

    if not update_fields:
        return jsonify({"message": "No valid fields to update"}), 400

    update_fields["updated_at"] = datetime.utcnow()
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


# ---------------------- UPLOAD PROFILE IMAGE (Save in MongoDB) ----------------------
@user_bp.route("/profile/upload", methods=["PUT", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def upload_profile_image():
    """
    Upload profile image → Encode Base64 → Save in MongoDB users.profile_image
    Returns a data URI so the frontend can display instantly.
    """
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        if "profileImage" not in request.files:
            return jsonify({"message": "No image provided"}), 400

        file = request.files["profileImage"]
        if file.filename == "":
            return jsonify({"message": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"message": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        unique_name = f"profile_{uuid.uuid4().hex}_{filename}"
        content_type = file.mimetype

        # Read image as Base64
        image_data = base64.b64encode(file.read()).decode("utf-8")
        image_uri = f"data:{content_type};base64,{image_data}"

        # Save directly in MongoDB under user's profile
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "profile_image": image_uri,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return jsonify({
            "message": "Profile image uploaded successfully",
            "profileImage": image_uri
        }), 200

    except Exception as e:
        print("❌ upload_profile_image error:", e)
        return jsonify({"message": "Failed to upload image"}), 500


# ---------------------- SET USER ROLE ----------------------
@user_bp.route("/profile/role", methods=["POST", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def set_role():
    """Save user type (Student / Employee)"""
    db = current_app.db
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    role = data.get("role")

    if role not in ["student", "employee"]:
        return jsonify({"error": "Invalid role"}), 400

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": role}})
    return jsonify({"message": "Role saved successfully", "role": role}), 200
