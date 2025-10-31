from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ✅ Import route blueprints
from routes.auth_routes import auth_bp
from routes.docs_routes import docs_bp
from routes.user_routes import user_bp
from routes.contact_routes import contact_bp
from routes.docai_routes import docai_bp
from routes.feedback_routes import feedback_bp
from routes.admin_routes import admin_bp
from routes.tools_routes import tools_bp
from routes.user_activity_routes import activity_bp

# ✅ Fixed: unique blueprint name
auth_bp = Blueprint("auth_bp", __name__)
load_dotenv()

# ✅ Initialize Flask App
app = Flask(__name__)

# ✅ Enable CORS for frontend communication (Production Safe)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                os.getenv("FRONTEND_ORIGIN", "https://viadocs.in"),
                "https://www.viadocs.in",
                "http://localhost:5173",  # local dev testing
            ]
        }
    },
    supports_credentials=True,
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Cache-Control",
        "Origin",
        "Accept",
    ],
    expose_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# ✅ JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "viadocs_jwt_secret")
jwt = JWTManager(app)

# ✅ MongoDB Connection
try:
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise Exception("Missing MONGODB_URI in environment variables.")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["viadocsDB"]
    app.db = db
    print("✅ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)
    app.db = None

# ✅ Register Blueprints (organized modular structure)
try:
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(docs_bp, url_prefix="/api/docs")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(contact_bp, url_prefix="/api/contact")
    app.register_blueprint(docai_bp, url_prefix="/api/docai")
    app.register_blueprint(feedback_bp, url_prefix="/api/feedback")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(tools_bp, url_prefix="/api/tools")
    app.register_blueprint(activity_bp, url_prefix="/api/activity")
    print("✅ All blueprints registered successfully!")
except ValueError as e:
    # Prevents duplicate blueprint crash on Railway
    print("⚠️ Blueprint registration issue detected:", e)

# ✅ Health Check Route
@app.route("/api/health")
def health():
    """Simple API health check"""
    return jsonify({
        "status": "ok",
        "db_connected": bool(app.db)
    }), 200

# ✅ Root Route (for direct browser access)
@app.route("/")
def home():
    return jsonify({
        "message": "🚀 Viadocs Backend Running Successfully",
        "frontend": os.getenv("FRONTEND_ORIGIN", "Not Set")
    }), 200

# ✅ Entry Point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 VIADOCS Backend running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
