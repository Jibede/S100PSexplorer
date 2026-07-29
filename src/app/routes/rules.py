from flask import Blueprint, redirect, render_template

from ..data_manager import DATA_ATTRS, DATA_RULES


rules_bp = Blueprint('rules', __name__, url_prefix='/rules')

@rules_bp.route("/")
@rules_bp.route("/<rule_code>")
def view_rules(rule_code: str = None):
    if rule_code is None:
        return redirect(f'/rules/{list(DATA_RULES.keys()[0])}')
    
    selected_attr = DATA_ATTRS.get(rule_code)
    
    return render_template(
        'rule.html',
        data=DATA_ATTRS,
        name_page='attributes',
        actual_element=rule_code,
        selected_attr=selected_attr,
    )