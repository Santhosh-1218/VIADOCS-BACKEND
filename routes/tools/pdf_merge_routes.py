import os
import io
from flask import Blueprint, request, send_file, jsonify
from PyPDF2 import PdfMerger

# Create blueprint for PDF Merge
pdf_merge_bp = Blueprint("pdf_merge_bp", __name__)

# Folder for uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "pdf-merge")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@pdf_merge_bp.route("", methods=["POST"])
def merge_pdfs():
    """
    Merge multiple PDF files into one.
    Expects multiple 'files' in form-data.
    Returns a merged PDF blob.
    """
    try:
        # ✅ Step 1: Get uploaded files
        uploaded_files = request.files.getlist("files")
        if not uploaded_files or len(uploaded_files) < 2:
            return jsonify({"error": "Please upload at least two PDF files"}), 400

        merger = PdfMerger()

        # ✅ Step 2: Merge all PDFs
        for file in uploaded_files:
            if not file.filename.lower().endswith(".pdf"):
                return jsonify({"error": f"Invalid file type: {file.filename}"}), 400

            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            merger.append(file_path)

        # ✅ Step 3: Write merged output to memory
        output_stream = io.BytesIO()
        merger.write(output_stream)
        merger.close()
        output_stream.seek(0)

        # ✅ Step 4: Optionally save for records
        merged_path = os.path.join(UPLOAD_FOLDER, "merged_output.pdf")
        with open(merged_path, "wb") as f:
            f.write(output_stream.getbuffer())

        # ✅ Step 5: Return merged PDF file
        output_stream.seek(0)
        return send_file(
            output_stream,
            as_attachment=True,
            download_name="merged.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        print(f"❌ PDF Merge Error: {e}")
        return jsonify({"error": str(e)}), 500
