import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from src.utils.logger import config_logger

logger = config_logger(__name__)

_SIMPLE_GROUPS = ["colorProfiles", "symbols", "styleSheets", "lineStyles", "areaFills", "rules"]


class XMLReaderPortrayal:
    def __init__(self, path: str, output_dir: str = "./data/portrayalCatalog"):
        self.file = Path(path)
        self.output_dir = Path(output_dir)
        
        if not self.file:
            logger.warning("No file found for this the pattern: %s", path)
    
    def get_info(self) -> None:
        logger.info("Processing %s", self.file)
        
        root = ET.parse(self.file).getroot()
        
        for element in root:
            tag = element.tag
            handler = self._dispatch(tag)
            
            if handler is None: continue
            
            data = handler(element)
            self.save_json(data, tag)
            
    def save_json(self, data: Any, file_name: str) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_file = self.output_dir / f"{file_name}.json"
        
        with open(json_file, 'w', encoding='utf-8') as fp:
            json.dump(data, fp, indent=2)
            
        logger.info("Wrote %s", json_file)
    
    
    def _dispatch(self, tag: str):
        if tag == "alertCatalog":
            return self._parse_alert_catalog
        
        if tag in _SIMPLE_GROUPS:
            return self._parse_simple_group
        
        if tag == "context":
            return self._parse_context
        
        if tag == "viewingGroups":
            return self._parse_vw_groups
        
        if tag == "displayPlanes":
            return self._parse_display_planes
        
        if tag == "viewingGroupLayers":
            return lambda el: self.get_viewing(el, "viewingGroup")
        
        if tag == "displayModes":
            return lambda el: self.get_viewing(el, "viewingGroupLayer")
        
        if tag == "foundationMode":
            return self._parse_foundation_mode
        
        return None
    
    def _parse_alert_catalog(self, e: Element) -> list[dict]:
        return [{
            "id": e.get('id'),
            **self.get_description_info(e),
            **self.get_file_info(e)
        }]
        
        
    def _parse_simple_group(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            rule_type_tag = e.find('ruleType')
            rule_type = rule_type_tag.text if rule_type_tag is not None else None
            
            entry = {
                "id": e.get("id"),
                **self.get_description_info(e),
                **self.get_file_info(e)
            }
            
            if rule_type: entry['rule_type'] = rule_type
            
            result.append(entry)
            
        return result
    
    def _parse_context(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            type_tag = e.find("type")
            default_tag = e.find("default")
            
            result.append({
                "id": e.get("id"),
                **self.get_description_info(e),
                "type": type_tag.text if type_tag is not None else None,
                "default": default_tag.text if default_tag is not None else None
            })
            
        return result
    
    
    def _parse_vw_groups(self, e: Element) -> list[dict]:
        return [{
            "id": vw.get("id"),
            **self.get_description_info(vw)
            }
            for vw in e
        ]
        
    def _parse_display_planes(self, e: Element) -> list[dict]:
                return [
            {
                "id": dp.get("id"),
                "order": dp.get("order"),
                **self.get_description_info(dp),
            }
            for dp in e
        ]

    def _parse_foundation_mode(self, e: Element) -> dict:
        return {
            "viewingGroup": [
                vw_gp.text for vw_gp in e.findall("viewingGroup")
            ]
        }

        
    @staticmethod
    def _text(e: Element, tag: str) -> str | None:
        found = e.find(tag)
        
        return found.text if found is not None else None
        
    def get_description_info(self, e: Element) -> dict:
        desc_group = e.find("description")
        
        if desc_group is None: return {"name": None, "description": None, "language": None}
        
        return {
            "name": self._text(desc_group, "name"),
            "description": self._text(desc_group, "description"),
            "language": self._text(desc_group, "language")
        }
        
    def get_file_info(self, e: Element) -> dict:
        return {
            "file_name": self._text(e, "fileName"),
            "file_type": self._text(e, "fileType"),
            "file_format": self._text(e, "fileFormat")
        }
    
    def get_viewing(self, vws: Element, vw_name: str = 'viewingGroup') -> list[dict]:
        result = []
        
        for vw in vws:
            result.append({
                "id": vw.get("id"),
                **self.get_description_info(vw),
                vw_name: [vw_gp.text for vw_gp in vw.findall(vw_name)]
            })

        return result
                            
if __name__ == "__main__":
    xml_reader = XMLReaderPortrayal("source/xml/portrayal_catalogue.xml")
    xml_reader.get_info()
