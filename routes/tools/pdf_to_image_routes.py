import os
import io
import zipfile
from flask import Blueprint, request, send_file, jsonify
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename

# Create blueprint for PDF → Image
pdf_to_image_bp = Blueprint("pdf_to_image_bp", __name__)

# Folder for uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-to-image")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Path to Poppler (⚠️ Update this path to your installed Poppler)
# Example for Windows:
POPPLER_PATH = r"C:\poppler-25.07.0\Library\bin"
# On Linux or Mac, you can remove the `poppler_path` argument entirely.


@pdf_to_image_bp.route("", methods=["POST"])
def pdf_to_image():
    """Convert a PDF file into individual images and return them as a ZIP."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        pdf_file = request.files["file"]
        if not pdf_file or pdf_file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Save uploaded PDF
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(pdf_path)

        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for i, img in enumerate(images, start=1):
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                zipf.writestr(f"page_{i}.png", img_bytes.read())

        zip_buffer.seek(0)

        # Remove uploaded PDF
        os.remove(pdf_path)

        # Send ZIP back to frontend
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name="pdf_images.zip",
            mimetype="application/zip"
        )

    except Exception as e:
        print(f"[ERROR] PDF to Image conversion failed: {e}")
        return jsonify({"error": "Failed to convert PDF", "details": str(e)}), 500
