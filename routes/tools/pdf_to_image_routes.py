import os
import io
import zipfile
from flask import Blueprint, request, send_file, jsonify
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from PIL import Image

# ✅ Create blueprint for PDF → Image
pdf_to_image_bp = Blueprint("pdf_to_image_bp", __name__)

# ✅ Folder for uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-to-image")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@pdf_to_image_bp.route("", methods=["POST"])
def pdf_to_image():
    """
    Convert uploaded PDF pages to images (optimized for Railway free tier).
    Returns a ZIP containing all pages as PNG images.
    """
    try:
        # ✅ Validate file presence
        if "file" not in request.files:
            return jsonify({"error": "No file part in request"}), 400

        pdf_file = request.files["file"]
        if not pdf_file or pdf_file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # ✅ Save uploaded file
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        pdf_file.save(pdf_path)

        # ✅ Optimize memory & disable Pillow bomb limit
        Image.MAX_IMAGE_PIXELS = None

        # ✅ Convert PDF to images (lower DPI for lightweight performance)
        try:
            images = convert_from_path(
                pdf_path,
                dpi=120,              # reduces memory & still readable
                fmt="png",            # output format
                thread_count=1        # prevent parallel memory usage
            )
        except Exception as e:
            print(f"[PDF2IMAGE] Conversion error: {e}")
            os.remove(pdf_path)
            return jsonify({"error": "Failed to convert PDF", "details": str(e)}), 500

        # ✅ Prepare ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for i, img in enumerate(images, start=1):
                try:
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    zipf.writestr(f"page_{i}.png", img_bytes.read())
                finally:
                    img.close()  # 🧹 Free memory after each page

        # ✅ Finalize buffer
        zip_buffer.seek(0)

        # ✅ Cleanup temporary file
        os.remove(pdf_path)

        print(f"[✅] Converted {filename} → {len(images)} images successfully")

        # ✅ Return ZIP file as response
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"{os.path.splitext(filename)[0]}_images.zip",
            mimetype="application/zip"
        )

    except MemoryError:
        print("[❌] Out of Memory during PDF → Image conversion")
        return jsonify({
            "error": "Server ran out of memory. Try smaller PDF or fewer pages."
        }), 500

    except Exception as e:
        print(f"[ERROR] PDF → Image conversion failed: {e}")
        return jsonify({
            "error": "Failed to convert PDF",
            "details": str(e)
        }), 500
