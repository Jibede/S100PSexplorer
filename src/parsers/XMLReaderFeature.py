import json
from pathlib import Path
from typing import Any
from venv import logger
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, ParseError
import xml.etree.ElementTree as ET
from src.utils.logger import config_logger

LOGGER = config_logger(__name__)

_BASE = "{http://www.iho.int/S100FC/5.2}"
_BASE2 = "{http://www.iho.int/S100Base/5.0}"
_XSI = "{http://www.w3.org/2001/XMLSchema-instance}"


class XMLReaderFeature:

    # Tags with simple informations
    _GENREAL_GROUPS = [
        "name",
        "scope",
        "fieldOfApplication",
        "versionNumber",
        "versionDate",
        "productId",
    ]

    # Parsing Handlers for each XML tag
    _HANDLERS = {
        **{gp: "_parse_general_groups" for gp in _GENREAL_GROUPS},
        "S100_FC_SimpleAttributes": "_parse_simple_attr",
        "S100_FC_ComplexAttributes": "_parse_complex_attr",
        "S100_FC_Roles": "_parse_roles",
        "S100_FC_InformationAssociations": "_parse_info_association",
        "S100_FC_FeatureAssociations": "_parse_feature_association",
        "S100_FC_InformationTypes": "_parse_info_type",
        "S100_FC_FeatureTypes": "_parse_feature_type",
    }

    def __init__(self, path: str, output_dir="./data/featureCatalog"):
        self.file = Path(path)
        self.output_dir = Path(output_dir)

        if not self.file.exists():
            LOGGER.error("No file found for this pattern: %s", path)

    def get_info(self) -> None:
        """The main function that gets the information from Feature Catalog and genarate parsed JSON files based on them"""

        LOGGER.info(f"{'#' * 30} GETTING FEATURE CATALOG DATA {'#' * 30}")

        root = self._get_root(self.file)
        if root is not None:
            LOGGER.warning("ERROR GETTING THE ROOT TREE. INTERRUPTING PROCESS !")
            return

        LOGGER.info(f"PROCESSING [{self.file}]")

        data = {}
        for element in root:
            tag = element.tag.split("}")[1]

            handler = self._dispatch(tag)

            if tag in self._GENREAL_GROUPS:
                data = data | handler(element, tag)

                if tag == self._GENREAL_GROUPS[-1]:
                    self._save_json(data, "genral_info.json")

                continue

            if handler is None:
                continue

            data = handler(element)
            self._save_json(data, f"{tag}.json")

        LOGGER.info(
            f"{'*' * 10} THE CAPTURE OF ALL INFORMATION FROM FEATURE CATALOG WAS COMPLETED {'*' * 10}"
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

        except ParseError as err:
            LOGGER.error(
                f"Error parsing the XML document from [{file}]. Error description: {err}"
            )
            return None

        except Exception as err:
            LOGGER.error(
                f"Error getting the root of the file [{file}]. Error description: {err}"
            )
            return None

    ########################################## READ AND WRITE FILES FUNCTION ############################################
    def _save_json(self, data: Any, file_name: str) -> None:
        """Save the data into a JSON file

        Args:
            data (Any): The data to be serialized
            file_name (str): The name of the file to create
        """

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            json_file = self.output_dir / f"{file_name}.json"

            with open(json_file, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)

            LOGGER.info(f"FILE [{json_file}] SUCCESSFULLY WRITTEN")

        except Exception as err:
            LOGGER.error(
                f"Error writing the file [{json_file}]. Error description: {err}"
            )

    ################################################################################################################

    def _dispatch(self, tag: str) -> callable:
        """Retrieves the appropriaten parsing handler for a given XML tag

        Args:
            tag (str): The XML tag name

        Returns:
            callable: The bound method responsible for parsing the tag
        """
        try:
            name = self._HANDLERS.get(tag)

            if name:
                return getattr(self, name)

            LOGGER.error(f"Parsing handler was not found for the tag [{tag}] !")
            return None

        except Exception as err:
            LOGGER.error(
                f"Error retriving the parsing handler for the tag [{tag}]. Error description: {err}"
            )
            return None

    @staticmethod
    def _find(e: Element, tag: str) -> Element | None:
        """Finds the first matching subelement with the specified tag

        Args:
            e (Element): The parent XML element to search within
            tag (str): The name of the tag to search for

        Returns:
            Element: The first matching subelement
        """
        try:
            for base in [_BASE, _BASE2]:
                found = e.find(f"{base}{tag}")

                if found is not None:
                    return found

            LOGGER.error(f"Element with tag [{tag}] was not found !")
            return None

        except TypeError as err:
            LOGGER.error(
                f"Error: The tag parameter must be a string [{tag}]. Error description: {err}"
            )
            return None

        except Exception as err:
            LOGGER.error(
                f"Error finding the element with tag [{tag}]. Error description: {err}"
            )
            return None

    def _findall(self, e: Element, tag: str) -> list[Element] | None:
        """Finds all matching subelements with the specified tag

        Args:
            e (Element): The parent XML element to search within
            tag (str): The name of the tah to search for

        Returns:
            list[Element] | None: A list of matching subelements
        """
        try:
            for base in [_BASE, _BASE2]:
                found = e.findall(f"{base}{tag}")

                if found is not None:
                    return found

            LOGGER.error(f"Elemenst with tag [{tag}] were not found !")
            return None

        except TypeError as err:
            LOGGER.error(
                f"Error: The tag parameter must be a string [{tag}]. Error description: {err}"
            )
            return None

        except Exception as err:
            LOGGER.error(
                f"Error finding the elements with tag [{tag}]. Error description: {err}"
            )
            return None

    def _text(self, e: Element, tag: str) -> str | None:
        """Extracts the text content of a specified subelement

        Args:
            e (Element): The parent XML element
            tag (str): The name of the subelement whose text is to be retrieved

        Returns:
            str: The text content of the subelement
        """

        try:
            found = self._find(e, tag)
            return found.text if found is not None else None

        except Exception as err:
            LOGGER.error(
                f"Error extracting the text content of subelement with tag [{tag}]. Error description: {err}"
            )
            return None

    def _get_attr(self, e: Element, tag: str, attr_name: str) -> str | int | None:
        """Retrives the value of a specific attribute from a subelement

        Args:
            e (Element): The parent XML element
            tag (str): The name of the subelement containing the attribute
            attr_name (str): The name of the attribute to retrieve

        Returns:
            str | int: The value of the attribute
        """

        try:
            attr = self._find(e, tag)
            return attr.attrib[attr_name] if attr is not None else None

        except KeyError as err:
            LOGGER.error(
                f"The attribute name [{attr_name}] was not found as attribute in element with tag [{tag}]. Error description: {err}"
            )
            return None

        except Exception as err:
            LOGGER.error(
                f"Error getting the value of the attribute [{attr_name}] from the element with tag [{tag}]. Error description: {err}"
            )
            return None

    ###################################################################################
    def _parse_general_groups(self, e: Element, tag: str) -> dict:
        return {tag: e.text}

    def _parse_simple_attr(self, element: Element) -> list[dict]:
        result = []
        list_val_arr = []

        for e in element:
            list_val_arr = []
            list_vals_group = self._find(e, "listedValues")
            if list_vals_group is not None:

                for val in list_vals_group:

                    list_val_arr.append(
                        {
                            "label": self._text(val, "label"),
                            "definition": self._text(val, "definition"),
                            "code": self._text(val, "code"),
                            "definition_reference": self.get_defenition_ref(val),
                        }
                    )

            result.append(
                {
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "code": self._text(e, "code"),
                    "alias": self._text(e, "alias"),
                    "value_type": self._text(e, "valueType"),
                    "definition_reference": self.get_defenition_ref(e),
                    "listed_value": list_val_arr,
                }
            )

        return result

    def _parse_complex_attr(self, element: Element) -> list[dict]:
        result = []

        for e in element:

            result.append(
                {
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "code": self._text(e, "code"),
                    "definition_reference": self.get_defenition_ref(e),
                    "sub_attr_binding": self.get_sub_attr_binding(
                        e, "subAttributeBinding"
                    ),
                }
            )

        return result

    def _parse_roles(self, element: Element) -> list[dict]:
        result = []

        for e in element:
            result.append(
                {
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "code": self._text(e, "code"),
                }
            )

        return result

    def _parse_info_association(self, element: Element) -> list[dict]:
        result = []

        for e in element:

            result.append(
                {
                    "is_abstract": self._get_attr(
                        element, "S100_FC_InformationAssociation", "isAbstract"
                    ),
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "code": self._text(e, "code"),
                    "definition_reference": self.get_defenition_ref(e),
                    "role": self._get_attr(e, "role", "ref"),
                }
            )

        return result

    def _parse_feature_association(self, element: Element) -> list[dict]:
        result = []

        for e in element:

            result.append(
                {
                    "is_abstract": self._get_attr(
                        element, "S100_FC_FeatureAssociation", "isAbstract"
                    ),
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "code": self._text(e, "code"),
                    "definition_reference": self.get_defenition_ref(e),
                    "role": [
                        attr.attrib.get("ref") for attr in self._findall(e, "role")
                    ],
                }
            )

        return result

    def _parse_info_type(self, element: Element) -> list[dict]:
        result = []

        for e in element:

            result.append(
                {
                    "is_abstract": self._get_attr(
                        element, "S100_FC_InformationType", "isAbstract"
                    ),
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "definition_reference": self.get_defenition_ref(e),
                    "attribute_binding": self.get_attr_binding(e),
                }
            )

        return result

    def _parse_feature_type(self, element: Element) -> list[dict]:
        result = []

        for e in element:

            result.append(
                {
                    "name": self._text(e, "name"),
                    "definition": self._text(e, "definition"),
                    "code": self._text(e, "code"),
                    "permitted_primitives": [
                        primitive.text
                        for primitive in self._findall(e, "permittedPrimitives")
                    ],
                    "definition_reference": self.get_defenition_ref(e),
                    "information_binding": self.get_info_binding(e),
                    "feature_binding": self.get_feature_binding(e),
                    "feature_use_type": self._text(e, "featureUseType"),
                    "attr_binding": self.get_sub_attr_binding(e, "attributeBinding"),
                }
            )

        return result

    ###################################################################################

    def get_defenition_ref(self, e: Element) -> dict | None:
        def_ref_group = self._find(e, "definitionReference")

        return (
            {
                "scr_identifier": self._text(def_ref_group, "sourceIdentifier"),
                "definition_ref": self._get_attr(
                    def_ref_group, "definitionSource", "ref"
                ),
            }
            if def_ref_group is not None
            else None
        )

    def get_multiplicity(self, e: Element) -> dict | None:
        multiplicity_group = self._find(e, "multiplicity")

        return {
            "lower": self._text(multiplicity_group, "lower"),
            "upper": (
                {
                    "xsi:nil": self._get_attr(
                        multiplicity_group, "upper", f"{_XSI}nil"
                    ),
                    "infinite": self._get_attr(multiplicity_group, "upper", "infinite"),
                    "value": self._text(multiplicity_group, "upper"),
                }
                if multiplicity_group is not None
                else None
            ),
        }

    def get_attr_binding(self, e: Element) -> list[dict]:
        result = []
        attrs_group = self._findall(e, "attributeBinding")

        for attr in attrs_group:

            result.append(
                {
                    "multiplicity": self.get_multiplicity(attr),
                    "attribute": self._get_attr(attr, "attribute", "ref"),
                }
            )

        return result

    def get_sub_attr_binding(self, e: Element, name) -> dict:
        result = []

        sub_attrs_group = self._findall(e, name)

        for sub_attr in sub_attrs_group:
            permited_vals = self._find(sub_attr, "permittedValues")

            result.append(
                {
                    "sequential": self._get_attr(
                        e, "subAttributeBinding", "sequential"
                    ),
                    "attribute": self._get_attr(sub_attr, "attribute", "ref"),
                    "multiplicity": self.get_multiplicity(sub_attr),
                    "permitted_values": (
                        [permited_val.text for permited_val in permited_vals]
                        if permited_vals is not None
                        else []
                    ),
                    "attribute_visibility": self._text(sub_attr, "attributeVisibility"),
                }
            )

        return result

    def get_info_binding(self, e: Element):
        info_binding = self._find(e, "informationBinding")

        if info_binding is None:
            return None

        return {
            "role_type": self._get_attr(e, "informationBinding", "roleType"),
            "multiplicity": self.get_multiplicity(info_binding),
            "association": self._get_attr(info_binding, "association", "ref"),
            "role": self._get_attr(info_binding, "role", "ref"),
            "feature_type": self._get_attr(info_binding, "featureType", "ref"),
        }

    def get_feature_binding(self, e: Element):
        feature_binding = self._find(e, "featureBinding")

        if feature_binding is None:
            return None

        return {
            "role_type": self._get_attr(e, "featureBinding", "roleType"),
            "multiplicity": self.get_multiplicity(feature_binding),
            "association": self._get_attr(feature_binding, "association", "ref"),
            "role": self._get_attr(feature_binding, "role", "ref"),
            "feature_type": self._get_attr(feature_binding, "featureType", "ref"),
        }
