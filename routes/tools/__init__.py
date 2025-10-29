from flask import Blueprint

# ✅ Create master blueprint for all tools
tools_bp = Blueprint("tools_bp", __name__)

# ✅ Import individual tool blueprints
from routes.tools.pdf_to_word_routes import pdf_to_word_bp
from routes.tools.word_to_pdf_routes import word_to_pdf_bp
from routes.tools.powerpoint_to_pdf_routes import powerpoint_to_pdf_bp
from routes.tools.excel_to_pdf_routes import excel_to_pdf_bp
from routes.tools.pdf_split_routes import pdf_split_bp
from routes.tools.pdf_merge_routes import pdf_merge_bp
from routes.tools.pdf_compress_routes import pdf_compress_bp
from routes.tools.pdf_to_image_routes import pdf_to_image_bp
from routes.tools.image_to_pdf_routes import image_to_pdf_bp
from routes.tools.password_protect_routes import password_protect_bp
from routes.tools.unlock_pdf_routes import unlock_pdf_bp

# ✅ Register all sub-blueprints with URL prefixes
tools_bp.register_blueprint(pdf_to_word_bp, url_prefix="/pdf-to-word")
tools_bp.register_blueprint(word_to_pdf_bp, url_prefix="/word-to-pdf")
tools_bp.register_blueprint(powerpoint_to_pdf_bp, url_prefix="/ppt-to-pdf")
tools_bp.register_blueprint(excel_to_pdf_bp, url_prefix="/excel-to-pdf")
tools_bp.register_blueprint(pdf_split_bp, url_prefix="/pdf-split")
tools_bp.register_blueprint(pdf_merge_bp, url_prefix="/pdf-merge")
tools_bp.register_blueprint(pdf_compress_bp, url_prefix="/pdf-compress")
tools_bp.register_blueprint(pdf_to_image_bp, url_prefix="/pdf-to-image")
tools_bp.register_blueprint(image_to_pdf_bp, url_prefix="/image-to-pdf")
tools_bp.register_blueprint(password_protect_bp, url_prefix="/password-protect")
tools_bp.register_blueprint(unlock_pdf_bp, url_prefix="/unlock-pdf")
