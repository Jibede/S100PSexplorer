import json
from typing import Dict, List
import glob
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pathlib import Path

from src.utils.logger import config_logger

LOGGER = config_logger(__name__)


class XMLReaderAditionalFiles:
    def __init__(self):
        self.file = None
        self.dir = None
        self.output_dir = None
        self.data = {}
        self.data_line = []
        self.symbols_related = {}

    def get_info(self, file_path: str):
        LOGGER.info(f"{'#' * 30} GETTING ADITIONAL FILES DATA {'#' * 30}")

        dt_related = self._read_json("data/related.json")
        self.symbols_related = dt_related['symbol']

        files = glob.glob(file_path)

        for file in files:
            self.data = {}
            self.data_line = []

            path = Path(file)
            self.file = path.stem
            self.dir = path.parent.name

            LOGGER.info(f"PROCESSING {self.dir} -> {self.file}")

            root = ET.parse(file).getroot()

            for e in root:
                self._dispatch(e)

            self._save_json(
                self.data_line if self.data_line else self.data,
                output=f"./data/aditionalFiles/{self.dir}",
                file_name=self.file,
            )

        self._save_json(
            dt_related, output="./data", file_name="related"
        )

        LOGGER.info(
            f"{'*' * 10} THE CAPTURE OF ALL INFORMATION FROM ADITIONAL FILES OF {self.dir.upper()} WAS COMPLETED {'*' * 10}"
        )

    def _read_json(self, path_file: str) -> None:
        with open(Path(path_file), "r", encoding="utf-8") as fp:
            return json.load(fp)

    def _save_json(self, data: List[Dict], output: str, file_name: str) -> None:
        output = Path(output)
        
        output.mkdir(parents=True, exist_ok=True)
        json_file = output / f"{file_name}.json"

        with open(json_file, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

    def _set_symbol_related(self, symbol_code: str, name_group: str) -> None:
        self.symbols_related.setdefault(symbol_code, {})
        self.symbols_related[symbol_code].setdefault(name_group, [])
        if self.file not in self.symbols_related[symbol_code][name_group]:
            self.symbols_related[symbol_code][name_group].append(self.file)

    def _dispatch(self, e: Element):
        if self.dir == "lineStyles":
            self._get_lineStyle(e)

        if self.dir == "areaFills":
            self._get_areFills(e)

        if self.dir == "colorProfiles":
            self._get_colorProfile(e)

    def _get_lineStyle(self, e: Element):
        tag = e.tag

        if tag == "intervalLength":
            self.data[tag] = e.text

        if tag == "pen":
            self.data[tag] = {
                "width": e.attrib.get("width"),
                "color": e.find("color").text,
            }

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
            self._set_symbol_related(ref, "line_styles")

        if tag == "lineStyle":
            self.data = {}
            for sub_e in e:
                self._get_lineStyle(sub_e)

            offset = e.attrib.get("offset")

            if offset:
                self.data["offset"] = offset
            self.data_line.append(self.data)

    def _get_areFills(self, e: Element):
        tag = e.tag

        if tag == "areaCRS":
            self.data[tag] = e.text

        if tag == "symbol":
            ref = e.attrib.get("reference")

            self.data[tag] = ref

            self._set_symbol_related(ref, "area_fills")

        if tag in ["v1", "v2"]:
            self.data[tag] = {"x": e.find("x").text, "y": e.find("y").text}

    def _get_colorProfile(self, e: Element):
        tag = e.tag

        if tag == "colors":
            colors = e.findall("color")

            for color in colors:
                token = color.attrib.get("token")
                name = color.attrib.get("name")
                description = color.find("description").text

                self.data.setdefault(token, {})["name"] = name
                self.data.setdefault(token, {})["description"] = description

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
