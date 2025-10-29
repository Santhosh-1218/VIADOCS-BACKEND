import os
import subprocess
import tempfile
import shutil
from flask import Blueprint, request, jsonify, send_file

word_to_pdf_bp = Blueprint("word_to_pdf_bp", __name__)

# Folder to save converted PDFs
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "word-to-pdf")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@word_to_pdf_bp.route("", methods=["POST"])
def convert_word_to_pdf():
    """
    Convert Word (.docx/.doc) to PDF using LibreOffice (headless mode).
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith((".docx", ".doc")):
        return jsonify({"error": "Invalid file type. Please upload .docx or .doc"}), 400

    # Create temp folder for conversion
    temp_dir = tempfile.mkdtemp()
    word_path = os.path.join(temp_dir, file.filename)
    file.save(word_path)

    try:
        # Run LibreOffice in headless mode to convert file
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                UPLOAD_FOLDER,
                word_path
            ],
            check=True
        )

        # Determine converted file path
        base_name = os.path.splitext(file.filename)[0]
        pdf_filename = f"{base_name}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Conversion failed: PDF not found")

        print(f"✅ Converted {file.filename} → {pdf_filename}")

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype="application/pdf"
        )

    except subprocess.CalledProcessError as e:
        print("❌ LibreOffice conversion failed:", e)
        return jsonify({"error": "LibreOffice conversion failed"}), 500

    except Exception as e:
        print("❌ Conversion Error:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
