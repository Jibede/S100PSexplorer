import json

from flask import Blueprint, redirect, render_template
from ..data_manager import DATA_FT, DATA_RULES, get_attr_info, get_ft_info


features_bp = Blueprint('features', __name__, url_prefix='/features')

@features_bp.route("/")
@features_bp.route("/<feature_code>")
def view_features(feature_code=None):
    if feature_code is None:
        return redirect(f"/features/{list(DATA_FT.keys())[0]}")

    selected_feature = DATA_FT.get(feature_code)
    
    return render_template(
        "feature.html",
        data=DATA_FT,
        name_page="features",
        actual_element=feature_code,
        selected_feature=selected_feature,
        get_attr_info=get_attr_info,
        get_info=get_ft_info,
        linked_rule=DATA_RULES.get(feature_code, []),
    )
