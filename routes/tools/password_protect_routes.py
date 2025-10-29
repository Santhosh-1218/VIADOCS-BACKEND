import os
from flask import Blueprint, request, jsonify, send_file
import pikepdf

# ✅ Blueprint
password_protect_bp = Blueprint("password_protect_bp", __name__)

# ✅ Upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "password-protect")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Check if PDF is password-protected
@password_protect_bp.route("/check", methods=["POST"])
def check_lock_status():
    """
    Check whether the uploaded PDF is locked or unlocked.
    """
    if "pdfFile" not in request.files:
        return jsonify({"message": "No PDF uploaded"}), 400

    pdf_file = request.files["pdfFile"]
    temp_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(temp_path)

    try:
        with pikepdf.open(temp_path):
            return jsonify({
                "locked": False,
                "message": "This PDF is unlocked and can be protected."
            }), 200
    except pikepdf.PasswordError:
        return jsonify({
            "locked": True,
            "message": "This PDF is already password-protected."
        }), 200
    except Exception as e:
        print(f"❌ PDF Check Error: {e}")
        return jsonify({"message": f"Error reading PDF: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ✅ Set password protection on an unlocked PDF
@password_protect_bp.route("", methods=["POST"])
def password_protect():
    """
    Protect an unlocked PDF with a new password.
    """
    if "pdf" not in request.files or "password" not in request.form:
        return jsonify({"message": "Missing file or password"}), 400

    pdf_file = request.files["pdf"]
    password = request.form["password"]

    temp_input = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, f"protected_{pdf_file.filename}")
    pdf_file.save(temp_input)

    try:
        with pikepdf.open(temp_input) as pdf:
            pdf.save(
                output_path,
                encryption=pikepdf.Encryption(owner=password, user=password, R=4)
            )

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"protected_{pdf_file.filename}",
            mimetype="application/pdf",
        )
    except pikepdf.PasswordError:
        return jsonify({"message": "This PDF is already protected."}), 400
    except Exception as e:
        print(f"❌ PDF Protect Error: {e}")
        return jsonify({"message": f"Error protecting PDF: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)
