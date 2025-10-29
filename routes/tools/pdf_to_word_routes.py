import os
import tempfile
from flask import Blueprint, request, jsonify, send_file
from pdf2docx import Converter

# Create Blueprint for PDF to Word route
pdf_to_word_bp = Blueprint("pdf_to_word_bp", __name__)

# Folder to store uploaded PDFs and converted DOCX files
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-to-word")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@pdf_to_word_bp.route("", methods=["POST"])
def convert_pdf_to_word():
    """
    Route: POST /api/tools/pdf-to-word
    Accepts: multipart/form-data (with 'file' field)
    Returns: converted Word (.docx) file for download
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

    try:
        # Save uploaded file temporarily
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)

        # Create output DOCX file path
        base_name = os.path.splitext(file.filename)[0]
        docx_filename = f"{base_name}.docx"
        docx_path = os.path.join(UPLOAD_FOLDER, docx_filename)

        # Convert using pdf2docx
        converter = Converter(pdf_path)
        converter.convert(docx_path)
        converter.close()

        # Send converted file for download
        return send_file(
            docx_path,
            as_attachment=True,
            download_name=docx_filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print("❌ Conversion Error:", str(e))
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

    finally:
        # Clean up uploaded PDF
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as cleanup_error:
            print("⚠️ Cleanup failed:", cleanup_error)
