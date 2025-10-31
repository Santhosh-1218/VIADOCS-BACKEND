import random
import smtplib
import os
import traceback
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
from bson import ObjectId
from utils.security import hash_password, check_password
from email.mime.text import MIMEText
from dotenv import load_dotenv

# ==========================================================
# ✅ Initialization
# ==========================================================
auth_bp = Blueprint("auth", __name__)
load_dotenv()

# ==========================================================
# 📧 Email + OTP Config
# ==========================================================
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
otp_store = {}

VALID_REFERRALS = {"DOC1", "DOC2", "DOC3", "DOC4", "DOC5",
                   "DOC6", "DOC7", "DOC8", "DOC9", "DOC10"}


def get_db():
    return current_app.db


# ==========================================================
# 🔍 CHECK USERNAME
# ==========================================================
@auth_bp.route("/check-username", methods=["GET"])
def check_username():
    try:
        username = request.args.get("username", "").strip().lower()
        if not username:
            return jsonify({"available": False, "error": "Missing username"}), 400

        db = get_db()
        exists = db.users.find_one({"username": username})
        return jsonify({"available": not bool(exists)}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"available": False, "error": str(e)}), 500


# ==========================================================
# 📧 CHECK EMAIL
# ==========================================================
@auth_bp.route("/check-email", methods=["GET"])
def check_email():
    """Check if an email already exists (used in forgot password)"""
    try:
        email = request.args.get("email", "").strip().lower()
        if not email:
            return jsonify({"error": "Missing email"}), 400

        db = get_db()
        exists = db.users.find_one({"email": email})

        # ✅ return key 'exists' instead of 'available'
        return jsonify({"exists": bool(exists)}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


# ==========================================================
# 🎟️ CHECK REFERRAL CODE
# ==========================================================
@auth_bp.route("/check-referral", methods=["GET"])
def check_referral():
    code = request.args.get("code", "").strip().upper()
    valid = code in VALID_REFERRALS
    return jsonify({"valid": valid}), 200


# ==========================================================
# 👤 REGISTER USER
# ==========================================================
@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user securely"""
    try:
        db = get_db()
        data = request.get_json()
        required = ["username", "first_name", "last_name",
                    "email", "password", "dob", "gender"]
        if not all(k in data and data[k] for k in required):
            return jsonify({"error": "Missing fields"}), 400

        # Duplicates
        if db.users.find_one({"email": data["email"].lower()}):
            return jsonify({"error": "Email already registered"}), 400
        if db.users.find_one({"username": data["username"].lower()}):
            return jsonify({"error": "Username already taken"}), 400

        # Referral validation
        referred_by = data.get("referred_by", "").strip().upper()
        if referred_by and referred_by not in VALID_REFERRALS:
            return jsonify({"error": "Invalid referral code"}), 400

        hashed_pw = hash_password(data["password"])

        db.users.insert_one({
            "username": data["username"].lower(),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data["email"].lower(),
            "password": hashed_pw,
            "original_password": data["password"],  # optional
            "dob": data["dob"],
            "gender": data["gender"],
            "referred_by": referred_by if referred_by else None,
            "plan": "Starter",
            "role": "user",
            "premium": False,
            "profile_image": None,
            "createdAt": datetime.utcnow()
        })

        print(f"✅ Registered user: {data['email']}")
        return jsonify({"message": "Account created successfully"}), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


# ==========================================================
# 🔐 LOGIN USER (User/Admin)
# ==========================================================
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        db = get_db()
        data = request.get_json()
        email = data.get("email", "").lower()
        password = data.get("password", "")

        ADMIN_EMAIL = "admin07@gmail.com"
        ADMIN_PASSWORD = "admin@viadocs.in"

        # Admin login
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            token = create_access_token(identity="admin", expires_delta=timedelta(hours=6))
            return jsonify({
                "token": token,
                "role": "admin",
                "redirect": "/admin/home",
                "message": "Admin login successful"
            }), 200

        # User login
        user = db.users.find_one({"email": email})
        if not user or not check_password(password, user["password"]):
            return jsonify({"message": "Invalid email or password"}), 401

        token = create_access_token(identity=str(user["_id"]), expires_delta=timedelta(hours=6))
        return jsonify({
            "token": token,
            "username": user["username"],
            "role": user.get("role", "user"),
            "redirect": "/home",
            "message": "User login successful"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Server error"}), 500


# ==========================================================
# 🧾 VERIFY TOKEN
# ==========================================================
@auth_bp.route("/verify", methods=["GET"])
@jwt_required()
def verify_user():
    """Check if JWT is valid"""
    try:
        db = get_db()
        user_id = get_jwt_identity()
        user = db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if not user:
            return jsonify({"loggedIn": False}), 404
        return jsonify({
            "loggedIn": True,
            "user": {"firstName": user.get("first_name", "User"),
                     "email": user.get("email", "")}
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"loggedIn": False, "error": str(e)}), 500


# ==========================================================
# 🔐 Forgot Password — OTP Flow
# ==========================================================

# 📤 Send OTP Email
def send_otp_email(recipient, otp):
    try:
        msg = MIMEText(f"""
Hello from Viadocs 👋,

Your 4-digit password reset OTP is: {otp}

This OTP expires in 5 minutes.

If you didn’t request this, please ignore.

— Team Viadocs
""")
        msg["Subject"] = "🔐 Viadocs Password Reset OTP"
        msg["From"] = EMAIL_USER
        msg["To"] = recipient

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print(f"✅ OTP email sent to {recipient}")
        return True
    except Exception as e:
        traceback.print_exc()
        print("❌ Email send failed:", e)
        return False

# 📩 Send OTP
@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    try:
        db = get_db()
        data = request.get_json()
        email = data.get("email", "").lower()

        if not email:
            return jsonify({"message": "Email is required"}), 400

        user = db.users.find_one({"email": email})
        if not user:
            return jsonify({"message": "Email not registered"}), 404

        otp = str(random.randint(1000, 9999))
        otp_store[email] = {
            "otp": otp,
            "expires": datetime.utcnow() + timedelta(minutes=5),
            "verified": False
        }

        print(f"🧾 OTP generated for {email}: {otp}")
        if not send_otp_email(email, otp):
            return jsonify({"message": "Failed to send OTP"}), 500

        return jsonify({"message": "OTP sent successfully!"}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500

# ✅ Verify OTP
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get("email", "").lower()
        otp = data.get("otp", "").strip()

        record = otp_store.get(email)
        if not record:
            return jsonify({"message": "No OTP found"}), 400
        if datetime.utcnow() > record["expires"]:
            otp_store.pop(email, None)
            return jsonify({"message": "OTP expired"}), 400
        if otp != record["otp"]:
            return jsonify({"message": "Invalid OTP"}), 400

        otp_store[email]["verified"] = True
        print(f"✅ OTP verified for {email}")
        return jsonify({"message": "OTP verified successfully!"}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500

# ✅ Reset Password (hashed)
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        db = get_db()
        data = request.get_json()
        email = data.get("email", "").lower()
        new_password = data.get("newPassword", "").strip()

        if not email or not new_password:
            return jsonify({"message": "Missing fields"}), 400

        record = otp_store.get(email)
        if not record or not record.get("verified"):
            return jsonify({"message": "OTP verification required"}), 400

        hashed_pw = hash_password(new_password)
        db.users.update_one({"email": email}, {"$set": {"password": hashed_pw}})

        otp_store.pop(email, None)
        print(f"✅ Password reset for {email}")
        return jsonify({"message": "Password reset successful!"}), 200
    except Exception:
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500