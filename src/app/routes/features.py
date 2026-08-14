from flask import Blueprint, render_template

from ..data_manager import DATA_FT, DATA_RULES, get_attr_info, get_ft_info


features_bp = Blueprint('features', __name__, url_prefix='/features')

@features_bp.route("/")
@features_bp.route("/<feature_code>")
def view_features(feature_code=f"{list(DATA_FT.keys())[0]}"):

    selected_feature = DATA_FT.get(feature_code)
    
    return render_template(
        "/features/main_feature.html",
        name_page="features",
        
        actual_element=feature_code,
        selected_feature=selected_feature,
        
        data=DATA_FT,
        linked_rule=DATA_RULES.get(feature_code, []),
        
        get_attr_info=get_attr_info,
        get_info=get_ft_info,
    )
