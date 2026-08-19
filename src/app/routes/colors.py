from flask import Blueprint, render_template

from ..data_manager import DATA_COLOR_PROFILES, DATA_COLORS_RELATED, DATA_LINE_STYLES, get_ft_info


colors_bp = Blueprint('colors', __name__, url_prefix='/colors')

@colors_bp.route('/')
@colors_bp.route('/<item_id>')
def view_color(item_id: str = f'{list(DATA_COLOR_PROFILES.keys())[0]}'):
    
    selected_item = DATA_COLOR_PROFILES.get(item_id)
    
    return render_template(
        'colors/main_colors.html',
        name_page='colors',
        
        selected_item=selected_item,
        actual_element=item_id,
        
        data=DATA_COLOR_PROFILES,
        data_line=DATA_LINE_STYLES,
        linked_colors=DATA_COLORS_RELATED,

        get_info=get_ft_info
    )