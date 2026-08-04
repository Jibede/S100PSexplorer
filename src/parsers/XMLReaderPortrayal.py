import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ParseError

from src.utils.logger import config_logger

LOGGER = config_logger(__name__)

# Groups with the same logic
_SIMPLE_GROUPS = ["colorProfiles", "symbols", "styleSheets", "lineStyles", "areaFills", "rules"]


class XMLReaderPortrayal:
    def __init__(self, path: str, output_dir: str = "./data/portrayalCatalog"):
        self.file = Path(path)
        self.output_dir = Path(output_dir)
        
        if not self.file.exists():
            LOGGER.error("No file found for this pattern: %s", path)
    
    def get_info(self) -> None:
        LOGGER.info(f'{'#' * 30} GETTING PORTRAYAL CATALOG DATA {'#' * 30}')
        
        root = self._get_root(self.file)
        if root is not None:
            LOGGER.warning("ERROR GETTING THE ROOT TREE. INTERRUPTING PROCESS !")
            return
        
        LOGGER.info(f'PROCESSING [{self.file}]')
        
        for element in root:
            tag = element.tag
            handler = self._dispatch(tag)
            
            if handler is None: continue
            
            data = handler(element)
            self.save_json(data, f'{tag}.json')
            
        LOGGER.info(f'{'*' * 10} THE CAPTURE OF ALL INFORMATION FROM PORTRAYAL CATALOG WAS COMPLETED {'*' * 10}')

    ############################################## READ AND WRITE FILES FUNCTION ################################################

    def _save_json(self, data: Any, file_name: str) -> None:
        """Save a list of dictionaries to a JSON file

        Args:
            data (List[Dict]): The data to be serialized
            output (str): The directory path where the file will be saved
            file_name (str): The name of the file to create
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            json_file = self.output_dir / f'{file_name}'

            with open(json_file, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)

            LOGGER.info(f"FILE [{json_file}] SUCCESSFULLY WRITTEN")

        except Exception as e:
            LOGGER.error(
                f"Error writing the file [{json_file}]. Error description: {e}"
            )
                    
    ############################################## TREE FUNCTIONS ###############################################################

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

    ######################################################## TREE FUNCTIONS #####################################################################
    @staticmethod
    def _text(e: Element, tag: str) -> str | None:
        """Extracts the text content of a specified subelement

        Args:
            e (Element): The parent XML element
            tag (str): The name of the subelement whose text is to be retrieved

        Returns:
            str: The text content of the subelement
        """

        try:
            found = e.find(tag)
            if found is not None:
                return found.text
                
            LOGGER.error(f'Element with tag [{tag}] was not found !')
            return None
            
        except Exception as err:
            LOGGER.error(
                f"Error extracting the text content of subelement with tag [{tag}]. Error description: {err}"
            )
            return None

    ######################################################## PARSE DATA FUNCTIONS #####################################################################

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
            return lambda el: self._get_viewing(el, "viewingGroup")
        
        if tag == "displayModes":
            return lambda el: self._get_viewing(el, "viewingGroupLayer")
        
        if tag == "foundationMode":
            return self._parse_foundation_mode
        
        return None
    
    def _parse_alert_catalog(self, e: Element) -> list[dict]:
        return [{
            "id": e.get('id'),
            **self._get_description_info(e),
            **self._get_file_info(e)
        }]
        
        
    def _parse_simple_group(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            rule_type_tag = e.find('ruleType')
            rule_type = rule_type_tag.text if rule_type_tag is not None else None
            
            entry = {
                "id": e.get("id"),
                **self._get_description_info(e),
                **self._get_file_info(e)
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
                **self._get_description_info(e),
                "type": type_tag.text if type_tag is not None else None,
                "default": default_tag.text if default_tag is not None else None
            })
            
        return result
    
    
    def _parse_vw_groups(self, e: Element) -> list[dict]:
        return [{
            "id": vw.get("id"),
            **self._get_description_info(vw)
            }
            for vw in e
        ]
        
    def _parse_display_planes(self, e: Element) -> list[dict]:
                return [
            {
                "id": dp.get("id"),
                "order": dp.get("order"),
                **self._get_description_info(dp),
            }
            for dp in e
        ]

    def _parse_foundation_mode(self, e: Element) -> dict:
        return {
            "viewingGroup": [
                vw_gp.text for vw_gp in e.findall("viewingGroup")
            ]
        }
    
    ######################################################## GROUP ELEMENTS FUNCTIONS #####################################################################
    
    def _get_description_info(self, e: Element) -> dict:
        desc_group = e.find("description")
        
        if desc_group is None: return {"name": None, "description": None, "language": None}
        
        return {
            "name": self._text(desc_group, "name"),
            "description": self._text(desc_group, "description"),
            "language": self._text(desc_group, "language")
        }
        
    def _get_file_info(self, e: Element) -> dict:
        return {
            "file_name": self._text(e, "fileName"),
            "file_type": self._text(e, "fileType"),
            "file_format": self._text(e, "fileFormat")
        }
    
    def _get_viewing(self, vws: Element, vw_name: str = 'viewingGroup') -> list[dict]:
        result = []
        
        for vw in vws:
            result.append({
                "id": vw.get("id"),
                **self._get_description_info(vw),
                vw_name: [vw_gp.text for vw_gp in vw.findall(vw_name)]
            })

        return result
