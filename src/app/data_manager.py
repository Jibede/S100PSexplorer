# src/app/data_menager.py

import json
from pathlib import Path
import re
from typing import Dict, List
import xml.etree.ElementTree as ET
from markupsafe import Markup

from ..utils.formatter import get_json
from ..utils.logger import config_logger

LOGGER = config_logger(__name__)

###################################################################################
#                          DATA MANAGEMENT & LOADING                              #
###################################################################################


def _load_data(file_path: Path) -> List[Dict] | Dict | None:
    """Reads and parses a JSON file from the data directory.

    Args:
        file_path (Path): The path to the JSON file.

    Returns:
        List[Dict] | Dict: The parsed JSON data.
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

        if key != "code":
            item["code"] = item.pop(key)

        result[dict_key] = item

    return result


def _get_linked_attrs() -> Dict[str, List[Dict]]:
    """Creates a dictionary mapping each attribute to its related features

    Returns:
        Dict[str, List[Dict]]: A dictionary grouping features by their shared attributess
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


###################################################################################
#                          GLOBAL PATHS & DATA INITIALIZATION                     #
###################################################################################

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
_data_view_group = _load_data(portrayal_dir / "viewingGroups.json")

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
DATA_SYMBOLS_RELATED = _load_data(base_dir / "related_symbols.json")
DATA_VW_RELATED = _load_data(base_dir / "related_vw.json")
DATA_COLORS_RELATED = _load_data(base_dir / "related_colors.json")
DATA_VIEW_GROUPS = _process_data(_data_view_group, "id")

###################################################################################
#                          SVG & UNIT TRANSFORMATIONS                             #
###################################################################################


def extract_svg_data(symbol_id: str) -> Dict[str, float]:
    """Extracts useful information from a specific svg to plot it

    Args:
        symbol_id (str): The id of the wanted photo

    Returns:
        Dict[str, float]: A dictionary with the offsets of the image for align with the line
    """
    svg = get_svg(symbol_id)
    root = ET.fromstring(svg)

    viewbox = root.attrib.get("viewBox", "0 0 0 0").split()
    min_x = float(viewbox[0]) if len(viewbox) == 4 else 0.0
    min_y = float(viewbox[1]) if len(viewbox) == 4 else 0.0

    pivot_cx = 0.0
    pivot_cy = 0.0
    for elem in root.iter():
        if elem.tag.endswith("circle") and "pivotPoint" in elem.attrib.get("class", ""):
            pivot_cx = float(elem.attrib.get("cx", "0"))
            pivot_cy = float(elem.attrib.get("cy", "0"))
            break

    offset_x = pivot_cx - min_x
    offset_y = pivot_cy - min_y

    return {
        "offset_x": transform_mm_px(offset_x),
        "offset_y": transform_mm_px(offset_y),
    }


def transform_mm_px(number: str | float) -> float:
    """Transforms milimeter into pixels

    Args:
        number (str | float): The number to be transformed

    Returns:
        float: The number in pixels
    """

    return float(number) * 96 / 25.4


def get_svg(symbol_id: str) -> Markup:
    """Gets a specific svg photo

    Args:
        symbol_id (str): The id of the wanted symbol

    Returns:
        Markup: The svg image
    """
    svg_path = symbols_svg_dir / f"{symbol_id}.svg"

    try:
        with open(svg_path, "r", encoding="utf=8") as fp:
            return Markup(fp.read())

    except FileNotFoundError:
        LOGGER.error(f"Path {svg_path} does not found !")
        return Markup(f"<span> File {symbol_id} does not found !</span>")


###################################################################################
#                          STYLE & ATTRIBUTE RETRIEVAL                            #
###################################################################################


def get_line_style(line_code: str) -> List[Dict]:
    """Gets the informations of a specific line_style

    Args:
        line_code (str): Code of the wanted line_style

    Returns:
        Dict: A dictionary with all useful and parsed informations of a line_style
    """
    line_path = aditional_dir / "lineStyles" / f"{line_code}.json"

    line_file = _load_data(line_path)
    line_file = line_file if isinstance(line_file, list) else [line_file]

    for line in line_file:
        line_color = line["pen"]["color"]
        line["pen"]["color_code"] = line_color
        line["pen"]["color"] = get_color_styles(line_color)

    return line_file


def get_area_fill(area_code: str) -> Dict:
    """Gets the information of a specific area_fill

    Args:
        area_code (str): Code of the wanted area_fill

    Returns:
        Dict: A dictionary with all useful informations of a area_fill
    """

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


###################################################################################
#                          FEATURE EXTRACTION & PARSING                           #
###################################################################################


def _extract_function_code(code: str) -> Dict | str:
    """_summary_

    Args:
        code (str): _description_

    Returns:
        Dict | str: _description_
    """
    match = re.search(r"^([^\(]+)\((.*)\)$", code)

    if match:
        return {"function": match.group(1).strip(), "param": match.group(2).strip()}

    return code


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

        elif instruction_type == "text_instruction":
            _get_ft_text_instruction(stmt, info)

    return info


###################################################################################
#                          INSTRUCTION-SPECIFIC PARSERS                           #
###################################################################################


def _get_ft_symbol_info(stmt: Dict[str, Dict], info: Dict) -> None:
    """Extracts symbol instruction data from a statement

    Args:
        stmt (Dict[str, Dict]): The statement containing instruction details and values
        info (Dict): The aggregated info dictionary being built for the results
    """

    instruction_type = stmt["instruction_type"]

    if instruction_type == "symbol":
        symbol_code = stmt.get("values", {}).get("PointInstruction")

        if isinstance(symbol_code, list):
            info.setdefault("symbol", []).extend(symbol_code)
        else:
            info.setdefault("symbol", []).append(
                {"value": symbol_code, "conditions": stmt.get("conditions")}
            )


from typing import Dict, Any


def _get_ft_line_info(stmt: Dict[str, Any], info: Dict[str, Any]) -> None:
    """Extracts simple line style information

    Args:
        stmt (Dict[str, Any]): The statement containing line style details
        info (Dict[str, Any]): The aggregated info dictionary being built for the results
    """
    info_line = {}
    values = stmt.get("values", {})

    for key, val in values.items():
        if isinstance(val, list):
            if key == "color":
                info_line["has_var"] = key
                info_line[key] = []

                for e in val:
                    color_data = {
                        **e,
                        'color_code': e.get('value'),
                        "rgb": get_color_styles(e.get("value")),
                    }
                    info_line[key].append(color_data)
            else:
                info_line.setdefault(key, []).extend(val)

        else:
            if key == "color":
                info_line["code"] = "SIMPLE LINE"
                info_line['color_code'] = val
                val = get_color_styles(val)

            info_line[key] = val

    info.setdefault("line_style", []).append(
        {**info_line, "type": "simple", "conditions": stmt.get("conditions", [])}
    )


def _get_ft_area_fill(stmt: Dict[str, Dict], info: Dict) -> None:
    """Extracts area fill instructions

    Args:
        stmt (Dict[str, Dict]): The statement containing area fill details
        info (Dict): The aggregated info dictionary being built for the results
    """
    area_code = stmt.get("values").get("AreaFillReference")

    info.setdefault("area_fill", []).append(
        {
            **get_area_fill(area_code),
            "value": area_code,
            "conditions": stmt.get("conditions"),
        }
    )


def _get_ft_color_fill(stmt: Dict[str, Dict], info: Dict) -> None:
    """Extracts color fill instrucions

    Args:
        stmt (Dict[str, Dict]): The statement containing color fill details
        info (Dict): The aggregated info dictionary being built for the results
    """
    data = stmt.get("values").get("ColorFill")
    transparency = 1

    if isinstance(data, str):
        color_code = data.split(",")

        # There's more parameters than just the color code
        if len(color_code) > 1:
            color_code, transparency = color_code
        else:
            color_code = color_code.pop()
    else:
        color_code: List[Dict] = data

    if isinstance(color_code, list):
        for color in color_code:

            color["code"] = color["value"]
            color["transparency"] = transparency

            color.update({"value": get_color_styles(color["code"])})

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


def _get_ft_line_instruction(stmt: Dict[str, Dict], info: Dict) -> None:
    """Extracts complex line instructions

    Args:
        stmt (Dict[str, Dict]): The statement containing line instructions details
        info (Dict): The aggregated info dictionary being built for the results
    """
    line_instruction = stmt.get("values").get("LineInstruction")

    if not line_instruction == "_simple_":
        info.setdefault("line_style", []).append(
            {
                "line_info": get_line_style(line_instruction),
                "type": "instruction",
                "code": line_instruction,
                "conditions": stmt.get("conditions"),
            }
        )


def _get_ft_text(stmt: Dict[str, Dict], info: Dict) -> None:
    """Extracts text rendering parameters

    Args:
        stmt (Dict[str, Dict]): The statement containing text rendering details
        info (Dict): The aggregated info dictionary being built for the results
    """
    values = stmt.get("values")

    info_text = {}
    for key, val in values.items():
        if key == "FontColor":
            if isinstance(val, list):
                info_text["has_var"] = key
                val = [{"code": item, **get_color_styles(item)} for item in val]
            else:
                val = {"code": val, **get_color_styles(val)}

        if isinstance(val, list):
            info_text["has_var"] = key
            info_text.setdefault(key, []).extend(val)

        else:
            info_text.setdefault(key, val)

    info.setdefault("text", []).append(
        info_text
        | {
            "line": stmt["line"],
            "code": _extract_function_code(stmt["code"]),
            "conditions": stmt.get("conditions"),
        }
    )

def _get_ft_text_instruction(stmt: Dict[str, Dict], info: Dict) -> None:
    """Extracts text instruction details

    Args:
        stmt (Dict[str, Dict]): The statement containing text instruction parameters.
        info (Dict): The aggregated info dictionary being built.
    """

    values = stmt.get("values")

    info_text = {}
    for key, val in values.items():
        if isinstance(val, list):
            info_text.setdefault(key, []).extend(val)

        else:
            info_text.setdefault(key, val)

    aditional_data = info_text | {
        "line_instruction": stmt["line"],
        "code_instruction": _extract_function_code(stmt["code"]),
    }

    if info.get("text"):
        info["text"][-1] |= aditional_data

    else:
        info.setdefault("text", []).append(aditional_data)
