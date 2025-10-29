import subprocess
import os

def libreoffice_convert(input_path, output_dir, output_format):
    """
    Convert documents using LibreOffice in headless mode.
    Automatically picks correct filters for better accuracy.
    """

    try:
        # 🧠 Step 1: Choose the right conversion filter
        if output_format == "docx":
            # PDF → DOCX
            convert_filter = "docx:MS Word 2007 XML"
        elif output_format == "pdf":
            # Word → PDF, Excel → PDF, PowerPoint → PDF
            convert_filter = "pdf:writer_pdf_Export"
        elif output_format == "xlsx":
            convert_filter = "xlsx:Calc MS Excel 2007 XML"
        elif output_format == "pptx":
            convert_filter = "pptx:Impress MS PowerPoint 2007 XML"
        else:
            # Default fallback (for unknown conversions)
            convert_filter = output_format

        # 🧩 Step 2: Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # 🧠 Step 3: Build the LibreOffice CLI command
        cmd = [
            "soffice",
            "--headless",
            "--convert-to", convert_filter,
            "--outdir", output_dir,
            input_path
        ]

        print("🚀 Running LibreOffice command:", " ".join(cmd))

        # 🧠 Step 4: Execute command and capture logs
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print("📤 LibreOffice STDOUT:", result.stdout)
        print("⚠️ LibreOffice STDERR:", result.stderr)

        # 🧠 Step 5: Verify output file exists
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + f".{output_format}"
        output_path = os.path.join(output_dir, output_filename)

        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output not found at {output_path}")

        print(f"✅ Conversion successful: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        raise Exception(f"LibreOffice conversion failed: {e}")
    except Exception as e:
        raise Exception(f"Error in libreoffice_convert: {e}")
