import os
import tempfile
import zipfile

from flask import Blueprint, current_app, jsonify, request, send_file

from ...utils.logger import config_logger

LOGGER = config_logger(__name__)

export_rules_bp = Blueprint('/export_rules', __name__)

@export_rules_bp.route('/export_rules', methods=["POST"])
def export_rules():
    
    selected_files = request.form.getlist('files_to_export')
    
    if not selected_files:
        return jsonify({'status': 'error', 'error': 'No files selected for export'})
    
    root_projet = os.path.abspath(os.path.join(current_app.root_path, '..',  '..', '..'))
    DATA_DIR = os.path.join(root_projet, 'raw', 'rules')
    
    if not os.path.exists(DATA_DIR):
        return jsonify({"status": "error", "error": "Data directory not found on server"}), 500
    
    try:
        temp_dir = tempfile.gettempdir()
        zip_filename = 'exported_files.zip'
        temp_zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(temp_zip_path, 'w') as zipf:
            for file_name in selected_files:
                
                file_path = os.path.join(DATA_DIR, file_name)
                
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=file_name)
                    
                else:
                    LOGGER.warning(f'{file_name} file was not found in the server !')
                    
        return send_file(
            temp_zip_path,
            as_attachment=True,
            download_name='exported_files.zip'
        )
        
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': f'Error: {str(e)}'}), 500