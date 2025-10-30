from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from bson import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import base64
import os
import uuid
from datetime import datetime

docs_bp = Blueprint("docs_bp", __name__)

# ----------------------------------------------------------
# CONFIG
# ----------------------------------------------------------
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------------------------------------
# CHECK DOCUMENT NAME
# ----------------------------------------------------------
@docs_bp.route("/check-name", methods=["POST", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def check_doc_name():
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
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def create_doc():
    try:
        db = current_app.db
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        name = data.get("name", "").strip()
        content = data.get("content", "")
        favorite = data.get("favorite", False)

        if not name:
            return jsonify({"message": "Document name required"}), 400

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
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def get_user_docs():
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
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def get_single_doc(doc_id):
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
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def update_doc(doc_id):
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
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def delete_doc(doc_id):
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
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def toggle_favorite(doc_id):
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        doc = db.documents.find_one({"_id": ObjectId(doc_id), "user_id": user_id})
        if not doc:
            return jsonify({"message": "Document not found"}), 404

        new_status = not doc.get("favorite", False)
        db.documents.update_one(
            {"_id": ObjectId(doc_id), "user_id": user_id},
            {"$set": {"favorite": new_status, "updated_at": datetime.utcnow()}},
        )

        return jsonify({"favorite": new_status}), 200
    except Exception as e:
        print("❌ toggle_favorite error:", e)
        return jsonify({"message": "Server error"}), 500


# ----------------------------------------------------------
# ✅ UPLOAD DOCUMENT IMAGE — Save to MongoDB Atlas
# ----------------------------------------------------------
@docs_bp.route("/upload-image", methods=["POST", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def upload_image():
    """
    Upload document image, encode in Base64, store in MongoDB Atlas,
    and return a data URI that can be rendered directly.
    """
    try:
        db = current_app.db
        user_id = get_jwt_identity()

        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400

        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        content_type = file.mimetype

        # Read file and encode to base64
        file_data = file.read()
        encoded = base64.b64encode(file_data).decode("utf-8")

        # Save in MongoDB
        db.images.insert_one({
            "user_id": user_id,
            "filename": unique_name,
            "content_type": content_type,
            "data": encoded,
            "uploaded_at": datetime.utcnow(),
        })

        # Create a data URI
        file_url = f"data:{content_type};base64,{encoded}"
        return jsonify({"url": file_url}), 200

    except Exception as e:
        print("❌ upload_image error:", e)
        return jsonify({"error": "Failed to upload image"}), 500


# ----------------------------------------------------------
# HOME SUMMARY
# ----------------------------------------------------------
@docs_bp.route("/summary", methods=["GET", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
@jwt_required()
def home_summary():
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
# AUTH REGISTER
# ----------------------------------------------------------
@docs_bp.route("/auth/register", methods=["POST", "OPTIONS"])
@cross_origin(origins=["https://viadocs.in"], supports_credentials=True)
def register():
    try:
        db = current_app.db
        data = request.get_json() or {}

        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()

        if not email or not password or not name:
            return jsonify({"message": "All fields are required"}), 400
        if "@" not in email:
            return jsonify({"message": "Invalid email"}), 400
        if db.users.find_one({"email": email}):
            return jsonify({"message": "User already exists"}), 400

        hashed_pw = generate_password_hash(password)
        result = db.users.insert_one({
            "email": email,
            "password": hashed_pw,
            "name": name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        return jsonify({"_id": str(result.inserted_id), "message": "User created"}), 201
    except Exception as e:
        print("❌ register error:", e)
        return jsonify({"message": "Server error"}), 500
