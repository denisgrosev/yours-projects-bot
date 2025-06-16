import subprocess
import os
import shutil

def convert(input_path, output_path=None):
    # Попробуем найти soffice
    soffice_path = shutil.which("soffice")
    if not soffice_path:
        # Попробуем дефолтный путь для Windows
        default_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
        if os.path.exists(default_path):
            soffice_path = default_path
        else:
            raise FileNotFoundError(
                "Не найден исполняемый файл LibreOffice (soffice.exe). "
                "Добавь LibreOffice в PATH или укажи абсолютный путь в libreoffice_converter.py"
            )
    output_dir = os.path.dirname(output_path) if output_path else os.path.dirname(input_path)
    subprocess.run([
        soffice_path, "--headless", "--convert-to", "pdf",
        "--outdir", output_dir, input_path
    ], check=True)

    if output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        generated_pdf = os.path.join(output_dir, base + ".pdf")
        if os.path.abspath(generated_pdf) != os.path.abspath(output_path):
            os.replace(generated_pdf, output_path)
