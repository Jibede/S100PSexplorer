import json

from flask import Blueprint, redirect, render_template

from ..data_manager import DATA_CONDITIONS, DATA_RULES, DATA_SYMBOLS, get_symbol_conditions


symbols_bp = Blueprint('symbols', __name__, url_prefix='/symbols')

@symbols_bp.route("/")
@symbols_bp.route("/<symbol_id>")
def view_symbols(symbol_id=None):

    if symbol_id is None:
        return redirect(f"/symbols/{list(DATA_SYMBOLS.keys())[0]}")

    selected_symbol = DATA_SYMBOLS.get(symbol_id)
    print(DATA_SYMBOLS)

    return render_template(
        "symbols.html",
        data=DATA_SYMBOLS,
        name_page="symbols",
        actual_element=symbol_id,
        selected_symbol=selected_symbol,
        linked_rules=DATA_CONDITIONS.get(symbol_id, []),
        get_symbol_conditions=get_symbol_conditions,
    )