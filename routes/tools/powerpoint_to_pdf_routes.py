import os
import subprocess
import tempfile
import shutil
from flask import Blueprint, request, jsonify, send_file

powerpoint_to_pdf_bp = Blueprint("powerpoint_to_pdf_bp", __name__)

# Folder for output PDFs
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "powerpoint-to-pdf")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@powerpoint_to_pdf_bp.route("", methods=["POST"])
def convert_ppt_to_pdf():
    """
    Convert PowerPoint (.ppt/.pptx) to PDF using LibreOffice (headless mode)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith((".ppt", ".pptx")):
        return jsonify({"error": "Invalid file type. Please upload .ppt or .pptx"}), 400

    # Save to temporary folder
    temp_dir = tempfile.mkdtemp()
    ppt_path = os.path.join(temp_dir, file.filename)
    file.save(ppt_path)

    try:
        # Run LibreOffice headless conversion
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                UPLOAD_FOLDER,
                ppt_path
            ],
            check=True
        )

        # Find the output PDF
        base_name = os.path.splitext(file.filename)[0]
        pdf_filename = f"{base_name}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Conversion failed: PDF not found")

        print(f"✅ Converted {file.filename} → {pdf_filename}")

        # Send file to frontend
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
        shutil.rmtree(temp_dir, ignore_errors=True)
