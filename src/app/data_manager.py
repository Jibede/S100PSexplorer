# app/data_menager.py

import json
from multiprocessing.util import LOGGER_NAME
from pathlib import Path
from turtle import color
from typing import Dict, List

from markupsafe import Markup

from ..utils.logger import config_logger

LOGGER = config_logger(__name__)

################### DATA MANAGER FUNCTIONS ###################


def _load_data(file_path: Path) -> list[dict] | dict | None:
    """Reads and parses a JSON file from the data directory.

    Args:
        file_path (Path): The path to the JSON file.

    Returns:
        list[dict] | dict: The parsed JSON data.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    except FileNotFoundError:
        LOGGER.error(f"The path [{file_path}] does not exist!")
        raise
    except Exception as e:
        LOGGER.error(e)
        raise


def _process_data(data: List[Dict], key: str = "code") -> Dict[str, Dict]:
    """Processes a list of dictionaries into an alphabetically ordered dictionary

    Args:
        data (List[Dict]): The input data to be processed
        key (str, optional): Key whose value becomes the top-level key in the returned dictionary. Defaults to 'code'.

    Returns:
        Dict[str, Dict]: A dictionary ordered alphabetically by the 'name' key
    """
    data.sort(key=lambda x: x.get("name", ""))

    result = {}
    for item in data:

        dict_key = item.get(key)

        if key not in item:
            LOGGER.error(f"[{key}] is not a key of the dataset !")
            return {}

        if key is not "code":
            item["code"] = item.pop(key)

        result[dict_key] = item

    return result


def _get_linked_attrs() -> dict[str, list[dict]]:
    """Creates a dictionary mapping each attribute to its related features

    Returns:
        dict[str, list[dict]]: A dictionary grouping features by their shared attributess
    """
    linked_attrs = {}

    for ft_dt in DATA_FT.values():
        for binding_attr in ft_dt.get("attr_binding", []):
            attr_name = binding_attr.get("attribute")

            if attr_name:
                linked_attrs.setdefault(attr_name, []).append(
                    {
                        "name": ft_dt.get("name"),
                        "code": ft_dt.get("code"),
                        "permitted_primitives": ft_dt.get("permitted_primitives"),
                    }
                )

    return linked_attrs


#############################################################

# PATH DIRECTORIES
base_dir = Path("data")
feature_dir = Path("data/featureCatalog")
portrayal_dir = Path("data/portrayalCatalog")
condition_dir = Path("data/rules_parsed")
aditional_dir = Path("data/aditionalFiles")
symbols_svg_dir = Path("src/app/static/symbols")

_data_ft_types = _load_data(feature_dir / "S100_FC_FeatureTypes.json")
_data_simple_attrs = _load_data(feature_dir / "S100_FC_SimpleAttributes.json")
_data_complex_attrs = _load_data(feature_dir / "S100_FC_ComplexAttributes.json")
_data_symbols = _load_data(portrayal_dir / "symbols.json")
_data_rules = _load_data(portrayal_dir / "rules.json")
_data_line_styles = _load_data(portrayal_dir / "lineStyles.json")
_data_area_fills = _load_data(portrayal_dir / "areaFills.json")

_all_attrs = _data_simple_attrs + [
    {**attr, "value_type": "complex"} for attr in _data_complex_attrs
]
DATA_ATTRS = _process_data(_all_attrs)
DATA_FT = _process_data(_data_ft_types)
DATA_RULES = _process_data(_data_rules, "id")
DATA_LINE_STYLES = _process_data(_data_line_styles, "id")
DATA_AREA_FILLS = _process_data(_data_area_fills, "id")
DATA_SYMBOLS = _process_data(_data_symbols, "id")
LINKED_ATTRS = _get_linked_attrs()
DATA_COLOR_PROFILES = _load_data(aditional_dir / "colorProfiles" / "colorProfile.json")
DATA_CONDITIONS = _load_data(base_dir / "related.json")

################### DATA TRANSFORM FUNCTIONS ###################


def get_svg(symbol_id: str):
    svg_path = symbols_svg_dir / f"{symbol_id}.svg"

    try:
        with open(svg_path, "r", encoding="utf=8") as fp:
            return Markup(fp.read())

    except FileNotFoundError:
        LOGGER.error(f"Path {svg_path} does not found !")
        return Markup(f"<span> File {symbol_id} does not found !</span>")


def get_line_style(line_code: str):
    line_path = aditional_dir / "lineStyles" / f"{line_code}.json"

    line_file = _load_data(line_path)

    line_color = line_file["pen"]["color"]
    line_file["pen"]["color"] = get_color_styles(line_color)

    return line_file


def get_area_fill(area_code: str):
    area_path = aditional_dir / "areaFills" / f"{area_code}.json"
    return _load_data(area_path)


def get_color_styles(color_code: str) -> Dict[str, Dict]:
    """Defines a dictionary with the RGB values for each day style

    Args:
        color_code (str): The color code to look up

    Returns:
        Dict[str, Dict]: A dictionary containing the RGB values for day, dusk and night
    """
    colors = {}
    for status in ["day", "dusk", "night"]:
        colors.setdefault(
            status, DATA_COLOR_PROFILES[color_code][f"rgb{status.capitalize()}"]
        )

    return colors


def get_attr_info(attr_code: str) -> Dict | None:
    """Gets the attribute data by its code

    Args:
        attr_code (str): The attribute code

    Returns:
        Dict | None: The data of the specific attribute
    """
    return DATA_ATTRS.get(attr_code)


def get_ft_info(ft_code: str) -> Dict[str, Dict]:
    """Extracts all inforamtion related to a specific feature

    Args:
        ft_code (str): The feature code

    Returns:
        Dict[str, Dict]: Dictionary with all related data
    """
    ft_conditions_path = condition_dir / ft_code / f"{ft_code}-conditions.json"
    stmts = _load_data(ft_conditions_path)

    info = {}
    for stmt in stmts:
        instruction_type = stmt["instruction_type"]

        if instruction_type == "symbol":
            _get_ft_symbol_info(stmt, info)

        elif instruction_type == "line_style":
            _get_ft_line_info(stmt, info)

        elif instruction_type == "area_fill":
            _get_ft_area_fill(stmt, info)

        elif instruction_type == "color_fill":
            _get_ft_color_fill(stmt, info)

        elif instruction_type == "line_instruction":
            _get_ft_line_instruction(stmt, info)

        elif instruction_type == "text":
            _get_ft_text(stmt, info)

    return info


def get_symbol_conditions(rule_code: str, symbol_code: str) -> List[str] | None:
    """Gets the conditions of a symbol in a specific rule

    Args:
        rule_code (str): The rule code
        symbol_code (str): The symbol code

    Returns:
        List[str] | None: A List of conditions
    """
    info = get_ft_info(rule_code)

    for symbol in info["symbol"]:
        if symbol.get("value") == symbol_code:
            return symbol.get("conditions")

    return None


################### FEATURES INFORMATION FUNCTIONS ###################


def _get_ft_symbol_info(stmt: Dict[str, Dict], info: Dict) -> None:
    instruction_type = stmt["instruction_type"]

    if instruction_type == "symbol":
        symbol_code = stmt.get("values", {}).get("PointInstruction")

        if isinstance(symbol_code, list):
            info.setdefault("symbol", []).extend(symbol_code)
        else:
            info.setdefault("symbol", []).append(
                {"value": symbol_code, "conditions": stmt.get("conditions")}
            )


def _get_ft_line_info(stmt: Dict[str, Dict], info: Dict):
    info_line = {}

    for key, val in stmt.get("values").items():
        if isinstance(val, list):
            if key == "color":

                color_data = {}
                for e in val:
                    color_data = {
                        **color_data,
                        **e,
                        "code": e["value"],
                        "color": get_color_styles(e["value"]),
                    }

                info_line.setdefault(key, []).append(color_data)

            else:
                info_line.setdefault(key, []).extend(val)

        else:
            if key == "color":
                info_line.setdefault("code", "SIMPLE LINE")
                val = get_color_styles(val)

            info_line.setdefault(key, val)

    info.setdefault("line_style", []).append(
        {**info_line, "type": "simple", "conditions": stmt.get("conditions")}
    )


def _get_ft_area_fill(stmt: Dict[str, Dict], info: Dict):
    area_code = stmt.get("values").get("AreaFillReference")

    info.setdefault("area_fill", []).append(
        {
            **get_area_fill(area_code),
            "value": area_code,
            "conditions": stmt.get("conditions"),
        }
    )


def _get_ft_color_fill(stmt: Dict[str, Dict], info: Dict):
    data = stmt.get("values").get("ColorFill")
    transparency = 1
    
    if isinstance(data, str):
        color_code = data.split(',')
        
        # There's more parameters than just the color code
        if len(color_code) > 1:
            color_code, transparency = color_code
        else:
            color_code = color_code.pop()
    else:
        color_code: List[Dict] = data
    

    if isinstance(color_code, list):
        for color in color_code:
            
            color['code'] = color['value']
            color['transparency'] = transparency
            
            
            color.update({
                'value': get_color_styles(color['code'])
            })
        
        
        info.setdefault("color_fill", []).extend(color_code)

    else:
        info.setdefault("color_fill", []).append(
            {
                "code": color_code,
                "value": get_color_styles(color_code),
                "transparency": transparency,
                "conditions": stmt.get("conditions"),
            }
        )


def _get_ft_line_instruction(stmt: Dict[str, Dict], info: Dict):
    line_instruction = stmt.get("values").get("LineInstruction")

    if not line_instruction == "_simple_":
        info.setdefault("line_style", []).append(
            {
                **get_line_style(line_instruction),
                "type": "instruction",
                "code": line_instruction,
                "conditions": stmt.get("conditions"),
            }
        )


def _get_ft_text(stmt: Dict[str, Dict], info: Dict):
    values = stmt.get("values")
    
    info_text = {}
    for key, val in values.items():
        if key == 'FontColor':
            if isinstance(val, list):
                val = [{'code':item, **get_color_styles(item)}  for item in val]
            else:
                val = {'code': val , **get_color_styles(val)}
        
        if isinstance(val, list):
            info_text.setdefault(key, []).extend(val)
        
        else:
            info_text.setdefault(key, []).append(
                {'value': val, 'conditions': stmt.get('conditions')}
            )
    
    info.setdefault('text', []).append(info_text | {'line': stmt['line'], 'code': stmt['code']})

#############################################################
