
from flask import Blueprint, render_template, request

from ..data_manager import DATA_COLOR_PROFILES, DATA_FT, DATA_RULES, get_ft_info

rules_bp = Blueprint('rules', __name__, url_prefix='/rules')

@rules_bp.route("/")
@rules_bp.route("/<item_id>")
def view_rules(item_id: str = f'{list(DATA_RULES.keys())[0]}'):
    
    selected_rule = DATA_RULES.get(item_id)
    theme = request.args.get('theme', 'day')

    
    return render_template(
        'rules/main_rules.html',
        name_page='rules',
         
        data=DATA_RULES,
        colors=DATA_COLOR_PROFILES,
        
        actual_element=item_id,
        selected_rule=selected_rule,
        info_rule=get_ft_info(item_id),
        linked_ft=DATA_FT.get(item_id, []),
        
        theme=theme
        
    )