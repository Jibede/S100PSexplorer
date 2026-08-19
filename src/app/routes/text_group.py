from flask import Blueprint, render_template

from ..data_manager import DATA_COLOR_PROFILES, DATA_FT, DATA_RULES, DATA_VIEW_GROUPS, DATA_VW_RELATED, get_ft_info

text_group_bp = Blueprint('text_group', __name__, url_prefix='/text_group')

@text_group_bp.route('/')
@text_group_bp.route('/<item_id>')
def view_text_group(item_id: str = f'{list(DATA_VIEW_GROUPS.keys())[0]}'):
    
    selected_item = DATA_VIEW_GROUPS.get(item_id)
    
    return render_template(
        'text_groups/main_text_group.html',
        name_page='text_group',
    
        data=DATA_VIEW_GROUPS,
        data_colors=DATA_COLOR_PROFILES,
        data_rules=DATA_RULES,
        data_ft=DATA_FT,
        linked_vw=DATA_VW_RELATED,
        
        selected_text_group=selected_item,
        actual_element=item_id,
        
        get_info=get_ft_info
        )