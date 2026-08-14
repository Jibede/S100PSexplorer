from flask import Blueprint, render_template

from ..data_manager import DATA_ATTRS, LINKED_ATTRS


attributes_bp = Blueprint('attributes', __name__, url_prefix='/attributes')

@attributes_bp.route("/")
@attributes_bp.route("/<attr_code>")
def view_attributes(attr_code: str = f'{list(DATA_ATTRS.keys())[0]}'):
    
    selected_attr = DATA_ATTRS.get(attr_code)
    
    return render_template(
        'attributes/main_attribute.html',
        name_page='attributes',
        
        data=DATA_ATTRS,
        selected_attr=selected_attr,
        
        actual_element=attr_code,
        linked_objs=LINKED_ATTRS.get(attr_code, [])
    )