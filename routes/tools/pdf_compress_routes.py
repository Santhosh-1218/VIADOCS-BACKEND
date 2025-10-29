import os
import subprocess
from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

# ✅ Blueprint setup
pdf_compress_bp = Blueprint("pdf_compress_bp", __name__)

# ✅ Folder for storing compressed files
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-compress")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@pdf_compress_bp.route("", methods=["POST", "OPTIONS"])
@jwt_required(optional=True)  # JWT optional for now (can be strict if you prefer)
def compress_pdf():
    """
    Compress a PDF file using Ghostscript.
    Expects multipart/form-data:
    - file: PDF file
    - mode: compression level (extreme / recommended / low)
    """
    # --- Handle CORS preflight (OPTIONS) ---
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS Preflight OK"}), 200

    try:
        # ✅ Validate file
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        filename = secure_filename(file.filename)
        if not filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400

        # ✅ Save input file
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        # ✅ Handle compression level
        mode = request.form.get("mode", "recommended").lower()
        settings_map = {
            "extreme": "/screen",      # smallest file size
            "recommended": "/ebook",   # good balance
            "low": "/printer"          # higher quality
        }
        pdf_setting = settings_map.get(mode, "/ebook")

        output_filename = f"compressed_{filename}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)

        # ✅ Determine Ghostscript command
        gs_executable = "gswin64c" if os.name == "nt" else "gs"
        gs_command = [
            gs_executable,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={pdf_setting}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ]

        # ✅ Run Ghostscript
        subprocess.run(gs_command, check=True)

        # ✅ Calculate file sizes
        original_size = os.path.getsize(input_path) / (1024 * 1024)
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)

        # ✅ Send compressed file back to frontend
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype="application/pdf",
        )
        response.headers["x-original-size-mb"] = f"{original_size:.2f}"
        response.headers["x-compressed-size-mb"] = f"{compressed_size:.2f}"

        print(f"✅ Compressed {filename}: {original_size:.2f}MB → {compressed_size:.2f}MB")

        return response

    except subprocess.CalledProcessError as e:
        print("❌ Ghostscript compression failed:", str(e))
        return jsonify({"error": "Compression failed. Ensure Ghostscript is installed."}), 500

    except Exception as e:
        print("❌ Server Error:", str(e))
        return jsonify({"error": f"Server error: {str(e)}"}), 500
