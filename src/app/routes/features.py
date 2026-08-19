from flask import Blueprint, render_template, request

from ..data_manager import DATA_FT, DATA_RULES, get_attr_info, get_ft_info


features_bp = Blueprint('features', __name__, url_prefix='/features')

@features_bp.route("/")
@features_bp.route("/<item_id>")
def view_features(item_id=f"{list(DATA_FT.keys())[0]}"):

    selected_feature = DATA_FT.get(item_id)
    theme = request.args.get('theme', 'day')
    
    return render_template(
        "/features/main_feature.html",
        name_page="features",
        
        actual_element=item_id,
        selected_feature=selected_feature,
        
        data=DATA_FT,
        linked_rule=DATA_RULES.get(item_id, []),
        
        get_attr_info=get_attr_info,
        get_info=get_ft_info,
        
        theme=theme
    )
