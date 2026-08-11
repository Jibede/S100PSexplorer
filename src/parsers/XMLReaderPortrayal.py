# src/parsers/XMLReaderPortrayal.py

import json
from pathlib import Path
from typing import Any, Callable, Dict, List
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ParseError

from src.utils.logger import config_logger

LOGGER = config_logger(__name__)

# Groups with the same logic
_SIMPLE_GROUPS = [
    "colorProfiles",
    "symbols",
    "styleSheets",
    "lineStyles",
    "areaFills",
    "rules",
]


class XMLReaderPortrayal:
    def __init__(self, path: str, output_dir: str = "./data/portrayalCatalog"):
        self.file = Path(path)
        self.output_dir = Path(output_dir)

        if not self.file.exists():
            LOGGER.error(f"No file found for this pattern: {path}")
            
    ###################################################################################
    #                            MAIN FUNCTION                                        #
    ###################################################################################
    
    def get_info(self) -> None:
        """The main function that gets the information from Portrayal Catalog and genarate parsed JSON files based on them"""

        LOGGER.info(f"{'#' * 30} GETTING PORTRAYAL CATALOG DATA {'#' * 30}")

        root = self._get_root(self.file)
        if root is None:
            LOGGER.warning("ERROR GETTING THE ROOT TREE. INTERRUPTING PROCESS !")
            return

        LOGGER.info(f"PROCESSING [{self.file}]")

        for element in root:
            tag = element.tag
            handler = self._dispatch(tag)

            if handler is None:
                continue

            data = handler(element)
            self._save_json(data, f"{tag}.json")

        LOGGER.info(
            f"{'#' * 10} THE CAPTURE OF ALL INFORMATION FROM PORTRAYAL CATALOG WAS COMPLETED {'#' * 10}"
        )
        
    ###################################################################################
    #                      READ AND WRITE FILES FUNCTION                              #
    ###################################################################################

    def _save_json(self, data: Any, file_name: str) -> None:
        """Save a list of dictionaries to a JSON file

        Args:
            data (List[Dict]): The data to be serialized
            output (str): The directory path where the file will be saved
            file_name (str): The name of the file to create
        """
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            json_file = self.output_dir / f"{file_name}"

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
            LOGGER.error(
                f"Error parsing the XML document from [{file}]. Error description: {e}"
            )
            return None

        except Exception as e:
            LOGGER.error(
                f"Error getting the root of the file [{file}]. Error description: {e}"
            )
            return None

    ###################################################################################
    #                            XML TRAVERSAL UTILITIES                              #
    ###################################################################################
    
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

            LOGGER.error(f"Element with tag [{tag}] was not found !")
            return None

        except Exception as err:
            LOGGER.error(
                f"Error extracting the text content of subelement with tag [{tag}]. Error description: {err}"
            )
            return None

    def _dispatch(self, tag: str) -> Callable:
        """Routes the XML element to the appropriate parsing function based on its tag.

        Args:
            tag (str): The XML tag to be evaluted.

        Returns:
            Callable: The corresponding parsing method
        """
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
    
    ###################################################################################
    #                        PORTRAYAL CATALOG PARSERS                                #
    ###################################################################################
    
    def _parse_alert_catalog(self, e: Element) -> List[Dict]:
        """Parses the alertCatalog XML element

        Args:
            e (Element): The alertCatalog XML element

        Returns:
            List[Dict]: A list containing a dictionary with the alert catalog's ID, desciption and file info
        """
        return [
            {
                "id": e.get("id"),
                **self._get_description_info(e),
                **self._get_file_info(e),
            }
        ]

    def _parse_simple_group(self, element: Element) -> List[Dict]:
        """Parses elements belonging to simple groups (e.g., colorProfiles, symbols, styleSheets, lineStyles, areaFills, rules)

        Args:
            element (Element): The parent XML element of the simple group

        Returns:
            List[Dict]: A list of dictionaries containing the parsed ID, description, file info and optional rule type for each child element
        """
        result = []

        for e in element:
            rule_type_tag = e.find("ruleType")
            rule_type = rule_type_tag.text if rule_type_tag is not None else None

            entry = {
                "id": e.get("id"),
                **self._get_description_info(e),
                **self._get_file_info(e),
            }

            if rule_type:
                entry["rule_type"] = rule_type

            result.append(entry)

        return result

    def _parse_context(self, element: Element) -> List[Dict]:
        """Parses the context XML element

        Args:
            element (Element): The context XML element

        Returns:
            List[Dict]: A list of dictionaries containing the ID, description, type and default value for each context child
        """
        result = []

        for e in element:
            type_tag = e.find("type")
            default_tag = e.find("default")

            result.append(
                {
                    "id": e.get("id"),
                    **self._get_description_info(e),
                    "type": type_tag.text if type_tag is not None else None,
                    "default": default_tag.text if default_tag is not None else None,
                }
            )

        return result

    def _parse_vw_groups(self, e: Element) -> List[Dict]:
        """Parses the viewingGroups XML element

        Args:
            e (Element): The viewingGroups XML element

        Returns:
            List[Dict]: A list of dictionaries containing the ID and description for each viewing group
        """
        return [{"id": vw.get("id"), **self._get_description_info(vw)} for vw in e]

    def _parse_display_planes(self, e: Element) -> List[Dict]:
        """Parses the displayPlanes XML element

        Args:
            e (Element): The displayPlanes XML element

        Returns:
            List[Dict]: A list of dictionaries containing the ID, order, and description for each display plane
        """
        return [
            {
                "id": dp.get("id"),
                "order": dp.get("order"),
                **self._get_description_info(dp),
            }
            for dp in e
        ]

    def _parse_foundation_mode(self, e: Element) -> Dict:
        """Parses the foundationMode XML element

        Args:
            e (Element): The foundationMode XML element

        Returns:
            Dict: A dictionary containing a list of viewing groups associated with the foundation mode
        """
        return {"viewingGroup": [vw_gp.text for vw_gp in e.findall("viewingGroup")]}

    ###################################################################################
    #                        METADATA EXTRACTION HELPERS                              #
    ###################################################################################
    
    def _get_description_info(self, e: Element) -> Dict:
        """Extracts description metadata from an XML element

        Args:
            e (Element): The XML element containing a 'description' subelement

        Returns:
            Dict: A dictionary with 'name', 'description', and 'language' keys
        """
        desc_group = e.find("description")

        if desc_group is None:
            return {"name": None, "description": None, "language": None}

        return {
            "name": self._text(desc_group, "name"),
            "description": self._text(desc_group, "description"),
            "language": self._text(desc_group, "language"),
        }

    def _get_file_info(self, e: Element) -> Dict:
        """Extracts file-related metada from an XML element

        Args:
            e (Element): The XML element containing file metadata subelements

        Returns:
            Dict: A dictionary with 'file_name', 'file_type', and 'file_format' keys
        """
        return {
            "file_name": self._text(e, "fileName"),
            "file_type": self._text(e, "fileType"),
            "file_format": self._text(e, "fileFormat"),
        }

    def _get_viewing(self, vws: Element, vw_name: str = "viewingGroup") -> List[Dict]:
        """Extracts viewing group or viewing group layer information from a list of elements

        Args:
            vws (Element): The parent XML element containing viewing subelements
            vw_name (str, optional): _description_. The tag name of the viewing elements to search for. Defaults to 'viewingGroup'.

        Returns:
            List[Dict]: A list of dicitionaires containing the ID, description, and nested viewing groups for each element
        """
        result = []

        for vw in vws:
            result.append(
                {
                    "id": vw.get("id"),
                    **self._get_description_info(vw),
                    vw_name: [vw_gp.text for vw_gp in vw.findall(vw_name)],
                }
            )

        return result
