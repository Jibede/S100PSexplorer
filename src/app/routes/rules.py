import json

from flask import Blueprint, redirect, render_template

from ..data_manager import DATA_ATTRS, DATA_FT, DATA_RULES, get_ft_info


rules_bp = Blueprint('rules', __name__, url_prefix='/rules')

@rules_bp.route("/")
@rules_bp.route("/<rule_code>")
def view_rules(rule_code: str = f'{list(DATA_RULES.keys())[0]}'):
    
    selected_rule = DATA_RULES.get(rule_code)
    print(json.dumps(get_ft_info(rule_code).get('text', 'NUL')[0]))
    
    return render_template(
        'rules.html',
        data=DATA_RULES,
        name_page='rules',
        actual_element=rule_code,
        selected_rule=selected_rule,
        info_rule=get_ft_info(rule_code),
        linked_ft=DATA_FT.get(rule_code, [])
    )