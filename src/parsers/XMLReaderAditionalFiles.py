import json
from typing import Dict, List
import glob
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pathlib import Path

# from src.utils.logger import config_logger


# logger = config_logger(__name__)


class XMLReaderAditionalFiles:
    def __init__(self):
        self.file = None
        self.dir = None
        self.output_dir = None
        self.data = {}
        self.data_line = []

    def get_info(self, file_path: str):
        files = glob.glob(file_path)
        
        for file in files:
            self.data = {}
            self.data_line = []
            
            path = Path(file)
            self.file = path.stem
            self.dir = path.parent.name

            # logger.info("Processing %s", file)

            root = ET.parse(file).getroot()

            for e in root:
                self._dispatch(e)

            
            self.save_json(self.data_line if self.data_line else self.data)

    def save_json(
        self, data: List[Dict], output: str = "./data/aditionalFiles"
    ) -> None:
        output_dir = Path(output)
        output_dir = output_dir / self.dir

        output_dir.mkdir(parents=True, exist_ok=True)
        json_file = output_dir / f"{self.file}.json"

        with open(json_file, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

    def _dispatch(self, e: Element):
        if self.dir == "lineStyles":
            self.get_lineStyle(e)

        if self.dir == "areaFills":
            self.get_areFills(e)

        if self.dir == "colorProfiles":
            self.get_colorProfile(e)

    def get_lineStyle(self, e: Element):
        tag = e.tag

        if tag == "intervalLength":
            self.data[tag] = e.text

        if tag == "pen":
            self.data[tag] = {"width": e.attrib.get("width"), "color": e.find("color").text}

        if tag == "dash":
            self.data.setdefault(tag, []).append({"start": e.find("start").text, "length": e.find("length").text})

        if tag == "symbol":
            self.data.setdefault(tag, []).append({"code": e.attrib.get("reference"), "position": e.find("position").text,})

        if tag == "lineStyle":
            self.data = {}
            for sub_e in e:
                self.get_lineStyle(sub_e)
            
            offset = e.attrib.get('offset')
            
            if offset:
                self.data['offset'] = offset
            self.data_line.append(self.data)

    def get_areFills(self, e: Element):
        tag = e.tag

        if tag == "areaCRS":
            self.data[tag] = e.text

        if tag == "symbol":
            self.data[tag] = e.attrib.get("reference")

        if tag in ["v1", "v2"]:
            self.data[tag] = {"x": e.find("x").text, "y": e.find("y").text}

    def get_colorProfile(self, e: Element):
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


if __name__ == "__main__":
    xml_reader = XMLReaderAditionalFiles()
    xml_reader.get_info("source/lineStyles/*.xml")
    # xml_reader.get_info("source/areaFills/*.xml")
    # xml_reader.get_info("source/colorProfiles/*.xml")