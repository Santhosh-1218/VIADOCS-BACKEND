import os
from flask import Blueprint, request, jsonify, send_file
import pikepdf

unlock_pdf_bp = Blueprint("unlock_pdf_bp", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "unlock-pdf")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Check if locked/unlocked
@unlock_pdf_bp.route("/check", methods=["POST"])
def check_lock_status():
    if "pdfFile" not in request.files:
        return jsonify({"message": "No PDF uploaded"}), 400

    pdf_file = request.files["pdfFile"]
    temp_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(temp_path)

    try:
        with pikepdf.open(temp_path):
            return jsonify({
                "locked": False,
                "message": "This PDF is already unlocked."
            })
    except pikepdf.PasswordError:
        return jsonify({
            "locked": True,
            "type": "user",
            "message": "This PDF is locked. Please enter the password to unlock."
        })
    except Exception as e:
        return jsonify({"message": f"Error reading PDF: {e}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ✅ Unlock a locked PDF
@unlock_pdf_bp.route("/unlock", methods=["POST"])
def unlock_pdf():
    if "pdfFile" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    pdf_file = request.files["pdfFile"]
    password = request.form.get("password", "")

    temp_input = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, f"unlocked_{pdf_file.filename}")
    pdf_file.save(temp_input)

    try:
        with pikepdf.open(temp_input, password=password) as pdf:
            pdf.save(output_path)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"unlocked_{pdf_file.filename}",
            mimetype="application/pdf",
        )
    except pikepdf.PasswordError:
        return jsonify({"message": "Incorrect password or unable to unlock PDF."}), 401
    except Exception as e:
        return jsonify({"message": f"Error unlocking PDF: {e}"}), 500
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)






