from email.mime import base
import io
import os
import shutil
import tempfile
from zipfile import ZipFile, BadZipFile

from pathlib import Path
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
from build_data import process_data

TARGET = {
    "AreaFills": "areaFills",
    "ColorProfiles": "colorProfiles",
    "LineStyles": "lineStyles",
    "Rules": "rules",
    "Symbols": "symbols",
}


def extract_data(zip_ref: ZipFile, output: str):
    output = Path(output)

    for file in zip_ref.namelist():

        dir_name = Path(file).parent.name

        if dir_name in TARGET:

            if dir_name == "Symbols":
                output = Path(os.path.join(current_app.root_path, "..")) / "static"

            source = zip_ref.open(file)
            base_dir = output / TARGET.get(dir_name)
            os.makedirs(base_dir, exist_ok=True)

            target_path = base_dir / os.path.basename(file)

            with open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)

        elif (
            "portrayal_catalogue" in file or "Feature_Catalogue" in file
        ) and file.endswith(".xml"):
            source = zip_ref.open(file)
            base_dir = Path(output) / "xml"
            os.makedirs(base_dir, exist_ok=True)

            target_path = base_dir / os.path.basename(file)

            with open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)

        elif file.endswith(".zip"):
            nested_zip_data = zip_ref.read(file)
            nested_zip_buffer = io.BytesIO(nested_zip_data)

            try:
                with ZipFile(nested_zip_buffer, "r") as nested_zip:
                    extract_data(nested_zip, output)
            except BadZipFile:
                continue


upload_file_bp = Blueprint("upload_file", __name__)


@upload_file_bp.route("/upload_file", methods=["POST"])
def upload_file():
    root_projet = os.path.abspath(os.path.join(current_app.root_path, "..", "..", ".."))
    DATA_DIR = os.path.join(root_projet, "source")
    os.makedirs(DATA_DIR, exist_ok=True)

    if "file" not in request.files:
        return jsonify({"status": "error", "error": "No file were sent"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"status": "error", "error": "No file selected"}), 400

    if file and file.filename.endswith(".zip"):
        try:
            filename = secure_filename(file.filename)
            temp_dir = tempfile.gettempdir()
            temp_zip_path = os.path.join(temp_dir, filename)

            file.save(temp_zip_path)

            with ZipFile(temp_zip_path, "r") as zip_ref:
                extract_data(zip_ref, DATA_DIR)

            os.remove(temp_zip_path)

            process_data()

            return (
                jsonify(
                    {
                        "status": "sucess",
                        "message": "The file was uploaded successfully",
                    }
                ),
                200,
            )

        except BadZipFile:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "The uploaded file is not a valid ZIP file",
                    }
                ),
                400,
            )
        except Exception as e:
            return jsonify({"status": "error", "error": f"Error : {str(e)}"}), 500

    else:
        return (
            jsonify({"status": "error", "error": "Only .zip files are accepted"}),
            400,
        )
