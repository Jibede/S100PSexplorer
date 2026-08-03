
from flask import Blueprint, redirect, render_template, request

from ..data_manager import DATA_AREA_FILLS, DATA_CONDITIONS, DATA_FT, DATA_LINE_STYLES, DATA_RULES, DATA_SYMBOLS, get_area_fill, get_line_style


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
        "visualisation.html",
        data_symbols=DATA_SYMBOLS,
        data_ft=DATA_FT,
        data_line=DATA_LINE_STYLES,
        data_area=DATA_AREA_FILLS,
        data_rules=DATA_RULES,
        name_page="visualisation",
        actual_element=item_id,
        visu_type=visu_type,
        selected_item=selected_item,
        linked_rules=DATA_CONDITIONS.get(visu_type).get(item_id, []),
        
        get_line=get_line_style,
        get_area=get_area_fill,
        
        theme=theme
    )