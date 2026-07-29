from flask import Blueprint, redirect, render_template

from ..data_manager import DATA_ATTRS, LINKED_ATTRS


attributes_bp = Blueprint('attributes', __name__, url_prefix='/attributes')

@attributes_bp.route("/")
@attributes_bp.route("/<attr_code>")
def view_attributes(attr_code: str = None):
    if attr_code is None:
        return redirect(f'/attributes/{list(DATA_ATTRS.keys())[0]}')
    
    selected_attr = DATA_ATTRS.get(attr_code)
    
    return render_template(
        'attribute.html',
        data=DATA_ATTRS,
        name_page='attributes',
        actual_element=attr_code,
        selected_attr=selected_attr,
        linked_objs=LINKED_ATTRS.get(attr_code, [])
    )