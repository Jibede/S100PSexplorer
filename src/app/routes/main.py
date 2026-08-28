import os
from pathlib import Path

from flask import Blueprint, current_app, redirect

main_bp = Blueprint("main", __name__, url_prefix="/")


@main_bp.route("/")
def home():

    return redirect("/features/")


@main_bp.app_context_processor
def files_export():

    root_projet = os.path.abspath(os.path.join(current_app.root_path, "..", "..", ".."))
    DATA_DIR = Path(root_projet) / "raw" / "rules"

    files = []
    if DATA_DIR.exists():
        files = os.listdir(DATA_DIR)

    return dict(files=files)