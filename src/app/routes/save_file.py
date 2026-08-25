# src/routes/save_file.py

import json
import os
from pathlib import Path

from flask import Blueprint, jsonify, request


save_file_bp = Blueprint('save_file', __name__)

@save_file_bp.route('/save_file', methods=['POST'])
def save_file():
    new_data = request.json
    file_name = new_data.get('file')
    
    base_rules = Path('data/rules_parsed')
    file_path = base_rules / f'{new_data.get('file')}/{file_name}-conditions.json'
    rule_path = Path('source') / 'rules' / f'{file_name}.lua'
    
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
                
                target_line = item.get('line')
                code_target = item.get('code')
            
        if not dict_updated:
            return jsonify({"status": "error", "message": "Line is not located in the JSON file."}), 404
        
        if not os.path.exists(rule_path):
            return jsonify({'status': 'error', 'message': f'Lua file is not located [{rule_path}]'}), 404
        
        with open(rule_path, 'r', encoding='utf-8') as f_lua:
            lua_lines = f_lua.readlines()
            
        line_idx = target_line - 1
        
        if 0 <= line_idx < len(lua_lines):
            original_line = lua_lines[line_idx]
            
            indentation = original_line[:len(original_line) - len(original_line.lstrip())]
            
            lua_lines[line_idx] = f"{indentation}{code_target}\n"
            
            with open(rule_path, 'w', encoding='utf-8') as f_lua:
                f_lua.writelines(lua_lines)
        else:
            return jsonify({'status': 'error', 'message': 'Line code do not founded'}), 400
        
        with open(file_path, 'w', encoding='utf-8') as fp:
            json.dump(data_list, fp, indent=2, ensure_ascii=False)
        
        return jsonify({'status': 'sucess'})
    
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)}), 500