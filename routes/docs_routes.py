from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from bson import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash  # added import
import os
import uuid
from datetime import datetime

docs_bp = Blueprint("docs_bp", __name__)

# ----------------------------------------------------------
# CONFIG
# ----------------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    """Check allowed image extensions"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------------------------------------
# CHECK DOCUMENT NAME
# ----------------------------------------------------------
@docs_bp.route("/check-name", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def check_doc_name():
    """Check if a document name already exists for this user"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        name = data.get("name", "").strip()

        if not name:
            return jsonify({"exists": False, "message": "Name is required"}), 400

        exists = db.documents.find_one({"user_id": user_id, "name": name}) is not None
        return jsonify({"exists": exists}), 200

    except Exception as e:
        print("❌ check_doc_name error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# CREATE DOCUMENT
# ----------------------------------------------------------
@docs_bp.route("/my-docs", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def create_doc():
    """Create a new document for the logged-in user"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        name = data.get("name", "").strip()
        content = data.get("content", "")
        favorite = data.get("favorite", False)

        if not name:
            return jsonify({"message": "Document name required"}), 400

        # Prevent duplicate names for this user
        if db.documents.find_one({"user_id": user_id, "name": name}):
            return jsonify({"message": "Document name already exists"}), 400

        doc = {
            "user_id": user_id,
            "name": name,
            "content": content,
            "favorite": favorite,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = db.documents.insert_one(doc)
        return jsonify({"_id": str(result.inserted_id), "message": "Document created"}), 201
    except Exception as e:
        print("❌ create_doc error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# GET ALL USER DOCUMENTS
# ----------------------------------------------------------
@docs_bp.route("/my-docs", methods=["GET", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def get_user_docs():
    """Return all documents for logged-in user"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        docs = list(db.documents.find({"user_id": user_id}).sort("updated_at", -1))
        for d in docs:
            d["_id"] = str(d["_id"])
            d["created_at"] = d.get("created_at", datetime.utcnow()).isoformat()
            d["updated_at"] = d.get("updated_at", datetime.utcnow()).isoformat()

        return jsonify(docs), 200
    except Exception as e:
        print("❌ get_user_docs error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# GET SINGLE DOCUMENT
# ----------------------------------------------------------
@docs_bp.route("/my-docs/<doc_id>", methods=["GET", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def get_single_doc(doc_id):
    """Return a single document for a user"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()
        doc = db.documents.find_one({"_id": ObjectId(doc_id), "user_id": user_id})

        if not doc:
            return jsonify({"message": "Document not found"}), 404

        doc["_id"] = str(doc["_id"])
        return jsonify(doc), 200
    except Exception as e:
        print("❌ get_single_doc error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# UPDATE DOCUMENT
# ----------------------------------------------------------
@docs_bp.route("/my-docs/<doc_id>", methods=["PUT", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def update_doc(doc_id):
    """Update document name/content/favorite"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        update_data = {
            "name": data.get("name"),
            "content": data.get("content"),
            "favorite": data.get("favorite", False),
            "updated_at": datetime.utcnow(),
        }

        result = db.documents.update_one(
            {"_id": ObjectId(doc_id), "user_id": user_id}, {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"message": "Document not found"}), 404

        return jsonify({"message": "Document updated successfully"}), 200
    except Exception as e:
        print("❌ update_doc error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# DELETE DOCUMENT
# ----------------------------------------------------------
@docs_bp.route("/my-docs/<doc_id>", methods=["DELETE", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def delete_doc(doc_id):
    """Delete a user’s document"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        result = db.documents.delete_one({"_id": ObjectId(doc_id), "user_id": user_id})
        if result.deleted_count == 0:
            return jsonify({"message": "Document not found"}), 404

        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        print("❌ delete_doc error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# TOGGLE FAVORITE
# ----------------------------------------------------------
@docs_bp.route("/my-docs/<doc_id>/favorite", methods=["PATCH", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def toggle_favorite(doc_id):
    """Toggle favorite status for a document"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        doc = db.documents.find_one({"_id": ObjectId(doc_id), "user_id": user_id})
        if not doc:
            return jsonify({"message": "Document not found"}), 404

        new_status = not doc.get("favorite", False)
        # Ensure we only update the document if it belongs to the logged-in user
        result = db.documents.update_one(
            {"_id": ObjectId(doc_id), "user_id": user_id},
            {"$set": {"favorite": new_status, "updated_at": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            return jsonify({"message": "Document not found or not owned by user"}), 404

        return jsonify({"favorite": new_status}), 200
    except Exception as e:
        print("❌ toggle_favorite error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# UPLOAD DOCUMENT IMAGE
# ----------------------------------------------------------
@docs_bp.route("/upload-image", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def upload_image():
    """Upload document image and return public URL"""
    try:
        if "image" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        # ✅ Save in /uploads/doc_images/
        upload_folder = os.path.join(current_app.root_path, "uploads", "doc_images")
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"doc_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        file_url = f"/uploads/doc_images/{filename}"
        return jsonify({"url": file_url}), 200
    except Exception as e:
        print("❌ upload_image error:", e)
        return jsonify({"error": "Failed to upload image"}), 500


# ----------------------------------------------------------
# HOME DASHBOARD SUMMARY
# ----------------------------------------------------------
@docs_bp.route("/summary", methods=["GET", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
@jwt_required()
def home_summary():
    """Return summary info for dashboard"""
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        total_docs = db.documents.count_documents({"user_id": user_id})
        favorite_count = db.documents.count_documents({"user_id": user_id, "favorite": True})

        recent_docs = list(
            db.documents.find({"user_id": user_id})
            .sort("updated_at", -1)
            .limit(5)
        )

        for doc in recent_docs:
            doc["_id"] = str(doc["_id"])
            doc["updated_at"] = doc.get("updated_at", datetime.utcnow()).isoformat()

        # small favorites preview for home page (limit to 5)
        favorite_docs = list(
            db.documents.find({"user_id": user_id, "favorite": True})
            .sort("updated_at", -1)
            .limit(5)
        )
        for f in favorite_docs:
            f["_id"] = str(f["_id"])
            f["updated_at"] = f.get("updated_at", datetime.utcnow()).isoformat()

        return jsonify({
            "total_docs": total_docs,
            "favorite_count": favorite_count,
            "recent_docs": recent_docs,
            "favorite_docs": favorite_docs,
        }), 200
    except Exception as e:
        print("❌ home_summary error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# AUTH: REGISTER (added)
# ----------------------------------------------------------
@docs_bp.route("/auth/register", methods=["POST", "OPTIONS"])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def register():
    """Register a new user: expects JSON { email, password, name }"""
    try:
        db = current_app.db
        data = request.get_json() or {}

        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()

        if not email:
            return jsonify({"message": "Email is required"}), 400
        if not password:
            return jsonify({"message": "Password is required"}), 400
        if not name:
            return jsonify({"message": "Name is required"}), 400

        # Basic email format check
        if "@" not in email or "." not in email:
            return jsonify({"message": "Invalid email format"}), 400

        # Check existing user
        if db.users.find_one({"email": email}):
            return jsonify({"message": "User with this email already exists"}), 400

        hashed_pw = generate_password_hash(password)

        user_doc = {
            "email": email,
            "password": hashed_pw,
            "name": name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = db.users.insert_one(user_doc)

        return jsonify({"_id": str(result.inserted_id), "message": "User created"}), 201
    except Exception as e:
        print("❌ register error:", e)
        return jsonify({"message": "Server error"}), 500
