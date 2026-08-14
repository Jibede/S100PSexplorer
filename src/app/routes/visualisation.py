
from flask import Blueprint, render_template, request
from ..data_manager import DATA_AREA_FILLS, DATA_COLOR_PROFILES, DATA_SYMBOLS_RELATED, DATA_FT, DATA_LINE_STYLES, DATA_RULES, DATA_SYMBOLS, get_area_fill, get_ft_info, get_line_style

visualisation_bp = Blueprint('visualisation', __name__, url_prefix='/visualisation')

@visualisation_bp.route("/")
@visualisation_bp.route("/<visu_type>/<item_id>")
def view_visualisation(visu_type='symbol', item_id=list(DATA_SYMBOLS.keys())[0]):

    if visu_type == 'symbol':
        dataset = DATA_SYMBOLS
    elif visu_type == 'line_style':
        dataset = DATA_LINE_STYLES
    elif visu_type == 'area_fill':
        dataset = DATA_AREA_FILLS

    selected_item = dataset.get(item_id)
    theme = request.args.get('theme', 'day')

    return render_template(
        "visualisation/main_visualisation.html",
        name_page="visualisation",
        visu_type=visu_type,
        
        data_symbols=DATA_SYMBOLS,
        data_ft=DATA_FT,
        data_line=DATA_LINE_STYLES,
        data_area=DATA_AREA_FILLS,
        data_rules=DATA_RULES,
        data_colors=DATA_COLOR_PROFILES,
        
        actual_element=item_id,
        selected_item=selected_item,
        linked_rules=DATA_SYMBOLS_RELATED.get(visu_type).get(item_id, []),
        
        get_info=get_ft_info,
        get_line=get_line_style,
        get_area=get_area_fill,
        
        theme=theme
    )