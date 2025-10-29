import os
import subprocess
import tempfile
import shutil
from flask import Blueprint, request, jsonify, send_file

# Create blueprint for Excel → PDF
excel_to_pdf_bp = Blueprint("excel_to_pdf_bp", __name__)

# Folder for converted PDFs
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "excel-to-pdf")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@excel_to_pdf_bp.route("", methods=["POST"])
def convert_excel_to_pdf():
    """
    Convert Excel (.xls / .xlsx) files to PDF using LibreOffice (headless mode).
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith((".xls", ".xlsx")):
        return jsonify({"error": "Invalid file type. Please upload .xls or .xlsx"}), 400

    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    excel_path = os.path.join(temp_dir, file.filename)
    file.save(excel_path)

    try:
        # Use LibreOffice to convert Excel → PDF
        subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                UPLOAD_FOLDER,
                excel_path,
            ],
            check=True,
        )

        # Generate output path
        base_name = os.path.splitext(file.filename)[0]
        pdf_filename = f"{base_name}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        if not os.path.exists(pdf_path):
            raise FileNotFoundError("Conversion failed: PDF not found")

        print(f"✅ Converted {file.filename} → {pdf_filename}")

        # Send file to frontend for download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype="application/pdf",
        )

    except subprocess.CalledProcessError as e:
        print("❌ LibreOffice conversion failed:", e)
        return jsonify({"error": "LibreOffice conversion failed"}), 500

    except Exception as e:
        print("❌ Conversion Error:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
