
from flask import Blueprint, render_template

from ..data_manager import DATA_COLOR_PROFILES, DATA_FT, DATA_RULES, get_ft_info

rules_bp = Blueprint('rules', __name__, url_prefix='/rules')

@rules_bp.route("/")
@rules_bp.route("/<rule_code>")
def view_rules(rule_code: str = f'{list(DATA_RULES.keys())[0]}'):
    
    selected_rule = DATA_RULES.get(rule_code)
    
    return render_template(
        'rules/main_rules.html',
        name_page='rules',
         
        data=DATA_RULES,
        colors=DATA_COLOR_PROFILES,
        
        actual_element=rule_code,
        selected_rule=selected_rule,
        info_rule=get_ft_info(rule_code),
        linked_ft=DATA_FT.get(rule_code, []),
        
    )