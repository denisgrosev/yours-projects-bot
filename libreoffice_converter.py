import subprocess
import os

def convert(input_path, output_path=None):
    output_dir = os.path.dirname(output_path) if output_path else os.path.dirname(input_path)
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf",
        "--outdir", output_dir, input_path
    ], check=True)

    if output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        generated_pdf = os.path.join(output_dir, base + ".pdf")
        if os.path.abspath(generated_pdf) != os.path.abspath(output_path):
            os.replace(generated_pdf, output_path)