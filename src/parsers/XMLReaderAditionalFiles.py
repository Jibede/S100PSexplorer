# src/parsers/XMLReaderAditionalFiles.py

import json
from typing import Dict, List
import glob
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ParseError
from pathlib import Path

from src.utils.logger import config_logger

LOGGER = config_logger(__name__)


class XMLReaderAditionalFiles:
    """This class is responsible for retrieving and parsing information from area fills, color profiles, and line styles."""

    def __init__(self):
        self.file = None
        self.dir = None
        self.output_dir = None
        self.data = {}
        self.data_line = []
        self.symbols_related = {}
        self.colors_related = {}

    ###################################################################################
    #                            MAIN FUNCTION                                        #
    ###################################################################################

    def get_info(self, file_path: str):
        """The main function that gets the information from [areaFills, colorProfiles and lineStyles] and generate JSON files for each

        Args:
            file_path (str): Path where can find all the XML files
        """
        LOGGER.info(f"{'#' * 30} GETTING ADITIONAL FILES DATA {'#' * 30}")

        dt_related = self._read_json(path_file="data/related_symbols.json")
        self.symbols_related = dt_related["symbol"]
        
        dt_related_color = self._read_json(path_file="data/related_colors.json")
        self.colors_related = dt_related_color["line_style"]
        
        files = glob.glob(file_path)

        for file in files:
            self.data = {}
            self.data_line = []

            path = Path(file)
            self.file = path.stem
            self.dir = path.parent.name

            root = self._get_root(file)
            if root is None:
                LOGGER.warning(
                    f"THE FILE {self.dir} -> {self.file} WON'T BE PROCESSED DUE TO AN ERROR"
                )
                continue

            LOGGER.info(f"PROCESSING [{self.dir} -> {self.file}]")

            for e in root:
                self._dispatch(e)

            self._save_json(
                self.data_line if self.data_line else self.data,
                output=f"./data/aditionalFiles/{self.dir}",
                file_name=f'{self.file}.json',
            )

        self._save_json(dt_related, output="./data", file_name="related_symbols.json")
        self._save_json(dt_related_color, output="./data", file_name="related_colors.json")

        LOGGER.info(
            f"{'*' * 10} THE CAPTURE OF ALL INFORMATION FROM ADITIONAL FILES OF {self.dir.upper()} WAS COMPLETED {'*' * 10}"
        )

    ###################################################################################
    #                      READ AND WRITE FILES FUNCTION                              #
    ###################################################################################

    def _read_json(self, path_file: str) -> Dict:
        """Reads and parsers a JSON file into a Python dictionary

        Args:
            path_file (str): The file path to the JSON file to be read

        Returns:
            Dict: A dictionary containing the parsed JSON data
        """
        try:
            with open(Path(path_file), "r", encoding="utf-8") as fp:
                return json.load(fp)

        except FileNotFoundError:
            LOGGER.error(f"No such file or diretory [{path_file}]")

        except Exception as e:
            LOGGER.error(
                f"Error reading the file [{path_file}]. Error description: {e}"
            )

    def _save_json(self, data: List[Dict], output: str, file_name: str) -> None:
        """Save a list of dictionaries to a JSON file

        Args:
            data (List[Dict]): The data to be serialized
            output (str): The directory path where the file will be saved
            file_name (str): The name of the file to create
        """
        try:
            output = Path(output)
            output.mkdir(parents=True, exist_ok=True)
            json_file = output / f"{file_name}"

            with open(json_file, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)

            LOGGER.info(f"FILE [{json_file}] SUCCESSFULLY WRITTEN")

        except Exception as e:
            LOGGER.error(
                f"Error writing the file [{json_file}]. Error description: {e}"
            )

    ###################################################################################
    #                               TREE FUNCTIONS                                    #
    ###################################################################################
    
    def _get_root(self, file: str) -> ElementTree:
        """Get the root element of a XML tree

        Args:
            file (str): The XML file

        Returns:
             ElementTree[str]: Root element of the tree
        """
        try:
            return ET.parse(file).getroot()

        except FileNotFoundError:
            LOGGER.error(f"No such file or diretory [{file}]")
            return None

        except ParseError as e:
            LOGGER.error(f'Error parsing the XML document from [{file}]. Error description: {e}')
            return None
            
        except Exception as e:
            LOGGER.error(f"Error getting the root of the file [{file}]. Error description: {e}")
            return None
    
    ###################################################################################
    #                        PROCESSING INFOMATIONS FUNCTIONS                         #
    ###################################################################################

    def _dispatch(self, e: Element) -> None:
        """Routes an element to the appropriate handler based on the current directory

        Args:
            e (Element): An element from the main tree
        """
        if self.dir == "lineStyles":
            self._get_lineStyle(e)

        if self.dir == "areaFills":
            self._get_areFills(e)

        if self.dir == "colorProfiles":
            self._get_colorProfile(e)

    def _get_lineStyle(self, e: Element) -> None:
        """Parses a line style XML element and extracts its configurantion

        Args:
            e (Element): The line style XML element to parse
        """
        tag = e.tag

        if tag == "intervalLength":
            self.data[tag] = e.text

        if tag == "pen":
            color = e.find("color").text
            self.data[tag] = {
                "width": e.attrib.get("width"),
                "color": color,
            }
            self._set_related(color, 'line_complex', self.colors_related)
            

        if tag == "dash":
            self.data.setdefault(tag, []).append(
                {"start": e.find("start").text, "length": e.find("length").text}
            )

        if tag == "symbol":
            ref = e.attrib.get("reference")
            self.data.setdefault(tag, []).append(
                {
                    "code": ref,
                    "position": e.find("position").text,
                }
            )
            self._set_related(ref, "line_styles", self.symbols_related)

        if tag == "lineStyle":
            self.data = {}
            for sub_e in e:
                self._get_lineStyle(sub_e)

            offset = e.attrib.get("offset")

            if offset:
                self.data["offset"] = offset
            self.data_line.append(self.data)

    def _get_areFills(self, e: Element) -> None:
        """Parses an area fill XML element and extracts its configurantion

        Args:
            e (Element): The area fill XML element to parse
        """
        tag = e.tag

        if tag == "areaCRS":
            self.data[tag] = e.text

        if tag == "symbol":
            ref = e.attrib.get("reference")

            self.data[tag] = ref

            self._set_related(ref, "area_fills", self.symbols_related)

        if tag in ["v1", "v2"]:
            self.data[tag] = {"x": e.find("x").text, "y": e.find("y").text}

    def _get_colorProfile(self, e: Element) -> None:
        """Parses a color profile XML element to extract color definitions and palettes

        Args:
            e (Element): The color profile XML element to parse
        """
        tag = e.tag

        if tag == "colors":
            colors = e.findall("color")

            for color in colors:
                token = color.attrib.get("token")
                name = color.attrib.get("name").capitalize()
                description = color.find("description").text

                self.data.setdefault(token, {})["name"] = name
                self.data.setdefault(token, {})["description"] = description
                self.data.setdefault(token, {})["code"] = token

        if tag == "palette":
            day_status = e.attrib.get("name")
            items = e.findall("item")

            for item in items:
                token = item.attrib.get("token")
                rgb = item.find("srgb")

                self.data.setdefault(token, {})[f"rgb{day_status}"] = {
                    "red": rgb.find("red").text,
                    "green": rgb.find("green").text,
                    "blue": rgb.find("blue").text,
                }

    
    ###################################################################################
    #                        PROCESSING RELATED FILE FUNTIONS                         #
    ###################################################################################

    def _set_related(self, symbol_code: str, name_group: str, data: Dict) -> None:
        """Maps the current file to a specific symbol code and group category.

        Args:
            symbol_code (str): The unique identifier or reference code for the symbol
            name_group (str): The category or context group where the symbol is
                being used (e.g., 'line_styles', 'area_fills')
        """
        data.setdefault(symbol_code, {})
        data[symbol_code].setdefault(name_group, [])
        if self.file not in data[symbol_code][name_group]:
            data[symbol_code][name_group].append(self.file)
