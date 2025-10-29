from flask import Flask, jsonify, send_from_directory
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
# ✅ Import all document tool routes (from routes/tools/)
from routes.tools_routes import tools_bp
from routes.user_activity_routes import activity_bp

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)

# ✅ Enable CORS for frontend communication
CORS(
    app,
    resources={r"/api/*": {"origins": os.getenv("FRONTEND_ORIGIN", "*")}},
    supports_credentials=True
)


# ✅ JWT Config
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "viadocs_jwt_secret")
jwt = JWTManager(app)

# ✅ MongoDB Connection
try:
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["viadocsDB"]
    app.db = db
    print("✅ Connected to MongoDB Atlas successfully!")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)
    app.db = None

# ✅ Register Blueprints (organized modular structure)
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(docs_bp, url_prefix="/api/docs")
app.register_blueprint(user_bp, url_prefix="/api")
app.register_blueprint(contact_bp, url_prefix="/api/contact")
app.register_blueprint(docai_bp, url_prefix="/api/docai")
app.register_blueprint(feedback_bp, url_prefix="/api/feedback")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

# ✅ Register all tool routes (PDF → Word, PDF → Image, etc.)
app.register_blueprint(tools_bp, url_prefix="/api/tools")
app.register_blueprint(activity_bp, url_prefix="/api/activity")

# ✅ Health Check Route
@app.route("/api/health")
def health():
    """Simple API health check"""
    return jsonify({
        "status": "ok",
        "db_connected": bool(app.db)
    }), 200


# ✅ Entry Point
if __name__ == "__main__":
    print("\n🚀 VIADOCS Backend is running...")
    print("📁 Tools folder active: PDF to Word, PDF to Image, Merge, Split, etc.")
    app.run(debug=True, port=5000)
