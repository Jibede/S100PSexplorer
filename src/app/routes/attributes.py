from flask import Blueprint, render_template

from ..data_manager import DATA_ATTRS, LINKED_ATTRS


attributes_bp = Blueprint('attributes', __name__, url_prefix='/attributes')

@attributes_bp.route("/")
@attributes_bp.route("/<item_id>")
def view_attributes(item_id: str = f'{list(DATA_ATTRS.keys())[0]}'):
    
    selected_attr = DATA_ATTRS.get(item_id)
    
    return render_template(
        'attributes/main_attribute.html',
        name_page='attributes',
        
        data=DATA_ATTRS,
        selected_attr=selected_attr,
        
        actual_element=item_id,
        linked_objs=LINKED_ATTRS.get(item_id, [])
    )