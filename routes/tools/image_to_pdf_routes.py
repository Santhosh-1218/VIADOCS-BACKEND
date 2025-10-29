import os
import io
from flask import Blueprint, request, send_file, jsonify
from werkzeug.utils import secure_filename
from PIL import Image

# --- Create blueprint for Image → PDF ---
image_to_pdf_bp = Blueprint("image_to_pdf_bp", __name__)

# --- Upload folder setup ---
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "image-to-pdf")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@image_to_pdf_bp.route("", methods=["POST"])
def image_to_pdf():
    """
    Convert multiple uploaded images into a single PDF file.
    """
    try:
        # ✅ Check for uploaded images
        if "images" not in request.files:
            return jsonify({"error": "No images uploaded"}), 400

        files = request.files.getlist("images")
        if not files or len(files) == 0:
            return jsonify({"error": "No valid images found"}), 400

        image_list = []
        first_image = None

        for idx, img_file in enumerate(files):
            if img_file and img_file.filename:
                filename = secure_filename(img_file.filename)
                img_path = os.path.join(UPLOAD_FOLDER, filename)
                img_file.save(img_path)

                # ✅ Open using Pillow and convert to RGB
                img = Image.open(img_path)
                rgb_img = img.convert("RGB")

                if idx == 0:
                    first_image = rgb_img
                else:
                    image_list.append(rgb_img)

        if not first_image:
            return jsonify({"error": "No valid images to process"}), 400

        # ✅ Save all images into a single PDF (in memory)
        pdf_buffer = io.BytesIO()
        first_image.save(pdf_buffer, format="PDF", save_all=True, append_images=image_list)
        pdf_buffer.seek(0)

        # ✅ Optional cleanup
        for f in os.listdir(UPLOAD_FOLDER):
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, f))
            except:
                pass

        # ✅ Send generated PDF to frontend
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="images.pdf"
        )

    except Exception as e:
        print(f"[ERROR] Image to PDF conversion failed: {e}")
        return jsonify({"error": "Failed to convert images to PDF", "details": str(e)}), 500
