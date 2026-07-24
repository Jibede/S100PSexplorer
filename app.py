from traceback import print_tb
from turtle import color
from typing import Dict, List
import json
from pathlib import Path
from flask import Flask, redirect, render_template

app = Flask(__name__)


def load_data(file_path: Path) -> List[Dict] | Dict:
    with open(file_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


feature_dir = Path("data/featureCatalog")
portrayal_dir = Path("data/portrayalCatalog")
condition_dir = Path("data/rules_parsed")
aditional_dir = Path("data/aditionalFiles")

feature_types = load_data(feature_dir / "S100_FC_FeatureTypes.json")
simple_attrs = load_data(feature_dir / "S100_FC_SimpleAttributes.json")
complex_attrs = load_data(feature_dir / "S100_FC_ComplexAttributes.json")
symbols = load_data(portrayal_dir / "symbols.json")
rules = load_data(portrayal_dir / "rules.json")
conditions = load_data(condition_dir / "symbol_rules.json")


def process_data(data: List[Dict], key: str = "code") -> Dict[str, Dict]:
    data.sort(key=lambda x: x.get("name", ""))
    return {item[key]: item for item in data}


symbols_by_code = process_data(symbols, 'id')

attrs = simple_attrs + [{**attr, "value_type": "complex"} for attr in complex_attrs]
attrs_by_code = process_data(attrs)

features_by_code = process_data(feature_types)

rules_by_id = process_data(rules, "id")

linked_attrs = {}
for ft_type in feature_types:
    feat_dt = {
        "name": ft_type.get("name"),
        "code": ft_type.get("code"),
        "permitted_primitives": ft_type.get("permitted_primitives"),
    }

    for binding_attr in ft_type.get("attr_biding", []):
        attr_name = binding_attr.get("attribute")

        if attr_name:
            if attr_name not in linked_attrs:
                linked_attrs[attr_name] = []
            linked_attrs[attr_name].append(feat_dt)


def get_attr_info(attr_code: str) -> Dict:
    return attrs_by_code.get(attr_code)


def get_info(feature_code: str) -> List[Dict]:
    feature_cond_path = condition_dir / feature_code / f"{feature_code}-conditions.json"

    if not feature_cond_path.exists():
        return []
    stmts = load_data(feature_cond_path)

    info = {}
    for stmt in stmts:
        instruction_type = stmt['instruction_type']
        
        if instruction_type == "symbol":
            symbol_code = stmt.get("values", {}).get("PointInstruction")

            if isinstance(symbol_code, list):
                info.setdefault('symbol', []).extend(symbol_code)
            else:
                info.setdefault('symbol', []).append(
                    {"value": symbol_code, "conditions": stmt.get("conditions")}
                )
                
        if instruction_type == 'line_style':
            color_path = aditional_dir / 'colorProfiles' / 'colorProfile.json'
            if not color_path.exists: return []
            
            color_file = load_data(color_path)
            
            
            info_line = {}
            for k, v in stmt.get('values').items():
                
                if isinstance(v, list):
                    if k == 'color':
                        dt =  [{**item, 'value': color_file[item['value']]['rgbNight']} for item in v]
                        
                        info_line.setdefault(k, []).append(dt[0])
                        
                    else:
                        info_line.setdefault(k, []).extend(v)
                    
                else:
                    if k == 'color': v = color_file[v]['rgbNight']
                        
                    info_line.setdefault(k, []).append(
                        {'vale': v, 'conditions': stmt.get('conditions')}
                    )
                
            info['line_style'] = info_line
            
        if instruction_type == 'area_fill':
            area_ref = stmt.get('values').get('AreaFillReference')
            area_path = aditional_dir / 'areaFills' / f'{area_ref}.json'
            if not area_path.exists: return []
            
            area_file = load_data(area_path)
            info.setdefault('area_fill', []).append(area_file | {'value': area_ref, 'conditions': stmt.get('conditions')})

    return info


def get_symbol_conditions(rule_code: str, symbol_code: str) -> List[str] | None:
    info = get_info(rule_code)
    
    for symbol in info['symbol']:
        if symbol.get('value') == symbol_code:
            return symbol.get("conditions")
        
    return None


# --- VIEWS ---

@app.route("/")
def home():
    return redirect("/features/")


# --- ATTRIBUTES ---

@app.route("/attributes")
@app.route("/attributes/")
@app.route("/attributes/<attr_code>")
def view_attributes(attr_code=None):
    if attr_code is None:
        return redirect(f"/attributes/{list(attrs_by_code.keys())[0]}")
        
    
    selected_attr = attrs_by_code.get(attr_code)

    return render_template(
        "attribute.html",
        data=attrs,
        name_page="attributes",
        actual_element=attr_code,
        selected_attr=selected_attr,
        linked_objs=linked_attrs.get(attr_code, []),
    )


# --- FEATURES ---


@app.route("/features")
@app.route("/features/")
@app.route("/features/<feature_code>")
def view_feature(feature_code=None):
    if feature_code is None:
        return redirect(f"/features/{list(features_by_code.keys())[0]}")

    selected_feature = features_by_code.get(feature_code)
    return render_template(
        "feature.html",
        data=feature_types,
        name_page="features",
        actual_element=feature_code,
        selected_feature=selected_feature,
        get_attr_info=get_attr_info,
        get_info=get_info,
        linked_rule=rules_by_id.get(feature_code, []),
    )


# --- SYMBOLS ---


@app.route("/symbols")
@app.route("/symbols/")
@app.route("/symbols/<symbol_id>")
def view_symbol(symbol_id=None):
    

    if symbol_id is None:
        return redirect(f"/symbols/{list(symbols_by_code.keys())[0]}")

    selected_symbol = symbols_by_code.get(symbol_id)

    return render_template(
        "symbols.html",
        data=symbols,
        name_page="symbols",
        actual_element=symbol_id,
        selected_symbol=selected_symbol,
        linked_rules=rules_by_id.get(symbol_id, []),
        get_symbol_conditions=get_symbol_conditions,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
