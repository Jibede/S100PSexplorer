# src/routes/save_file.py

import json
import os
from pathlib import Path

from flask import Blueprint, jsonify, request


save_file_bp = Blueprint('save_file', __name__)

@save_file_bp.route('/save_file', methods=['POST'])
def save_file():
    new_data = request.json
    
    base_rules = Path('data/rules_parsed')
    file_path = base_rules / f'{new_data.get('file')}/{new_data.get('file')}-conditions.json'
    
    data = dict(list(new_data.items())[1:])
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "File not found"}), 404
    
    
    try:
        with open(file_path, 'r', encoding='utf-8') as fp:
            data_list = json.load(fp)
            
        dict_updated = False
        for item in data_list:
            inst_type = item.get('instruction_type')
            if inst_type in data.keys() and item.get('line') == data.get(inst_type).get('line'):
                item.update(data.get(inst_type))
                
                dict_updated = True
            
        if not dict_updated:
            return jsonify({"status": "error", "message": "Linha não encontrada no JSON."}), 404
        
        with open(file_path, 'w', encoding='utf-8') as fp:
            json.dump(data_list, fp, indent=2, ensure_ascii=False)
        
        return jsonify({'status': 'sucess'})
    
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500