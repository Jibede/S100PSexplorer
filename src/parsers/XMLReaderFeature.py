import json
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
from src.utils.logger import config_logger

logger = config_logger(__name__)


_BASE = '{http://www.iho.int/S100FC/5.2}'
_BASE2 = '{http://www.iho.int/S100Base/5.0}'
_XSI = '{http://www.w3.org/2001/XMLSchema-instance}'


class XMLReaderFeature:
    
    _GENREAL_GROUPS = [
        'name',
        'scope',
        'fieldOfApplication',
        'versionNumber',
        'versionDate',
        'productId',
    ]
    _HANDLERS = {
        **{gp : '_parse_general_groups' for gp in _GENREAL_GROUPS},
        'S100_FC_SimpleAttributes': '_parse_simple_attr',
        'S100_FC_ComplexAttributes': '_parse_complex_attr',
        'S100_FC_Roles': '_parse_roles',
        'S100_FC_InformationAssociations': '_parse_info_association',
        'S100_FC_FeatureAssociations': '_parse_feature_association',
        'S100_FC_InformationTypes': '_parse_info_type',
        'S100_FC_FeatureTypes': '_parse_feature_type'
        
    }
    
    def __init__(self, path: str, output_dir = './data/featureCatalog'):
        self.file = Path(path)
        self.output_dir = Path(output_dir)
        
        if not self.file.exists():
            logger.warning("No file found for this pattern: %s", path)
            
    def get_info(self) -> None:
        logger.info("Processing %s", self.file)
        
        try:
            root = ET.parse(self.file).getroot()
            
        except (ET.ParseError, FileNotFoundError) as e:
            logger.error("Failed to parse %s: %s", self.file, e)
            return
        
        data = {}
        for element in root:
            tag = element.tag.split('}')[1]
            
            handler = self._dispatch(tag)
            
            if tag in self._GENREAL_GROUPS:
                data = data | handler(element, tag)
                
                if tag == self._GENREAL_GROUPS[-1]:self.save_json(data, 'genral_info')
                    
                continue
            
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
        name = self._HANDLERS.get(tag)
        
        return getattr(self, name) if name else None
        
    ###################################################################################
    @staticmethod
    def _find(e: Element, tag: str) -> Element | None:
        found = e.find(f'{_BASE}{tag}')
        
        if found is not None: return found
        
        return e.find(f'{_BASE2}{tag}')
    
    def _findall(self, e: Element, tag: str) -> list[Element] | None:
        found = e.findall(f'{_BASE}{tag}')
        
        if found: return found
        
        return e.findall(f'{_BASE2}{tag}')

    def _text(self, e: Element, tag: str) -> str | None:
        found = self._find(e, tag)
        
        return found.text if found is not None else None
    
    def _get_attr(self, e: Element, tag: str, attr_name: str) -> str | int:
        attr = self._find(e, tag)
        
        return attr.attrib.get(attr_name) if attr is not None else None
    
    ###################################################################################
    def _parse_general_groups(self, e: Element, tag: str) -> dict:
        return {tag: e.text}
    
    def _parse_simple_attr(self, element: Element) -> list[dict]:
        result = []
        list_val_arr = []
        
        for e in element:
            list_val_arr = []
            list_vals_group = self._find(e, 'listedValues')
            if list_vals_group is not None:
                
                for val in list_vals_group:
                    
                    list_val_arr.append({
                        'label': self._text(val, 'label'),
                        'definition': self._text(val, 'definition'),
                        'code': self._text(val, 'code'),
                        "definition_reference": self.get_defenition_ref(val)
                    })
                
                
            result.append({
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                'code': self._text(e, 'code'),
                'alias': self._text(e, 'alias'),
                "value_type": self._text(e, 'valueType'),
                "definition_reference": self.get_defenition_ref(e),
                'listed_value': list_val_arr
            })
            
        
        return result
    
    def _parse_complex_attr(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            
            result.append({
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                'code': self._text(e, 'code'),
                "definition_reference": self.get_defenition_ref(e),
                'sub_attr_binding': self.get_sub_attr_binding(e, 'subAttributeBinding')
            })
            
        return result
    
    def _parse_roles(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            result.append({
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                'code': self._text(e, 'code'),
            })
            
        return result
    
    def _parse_info_association(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            
            result.append({
                'is_abstract': self._get_attr(element, 'S100_FC_InformationAssociation', 'isAbstract'),
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                'code': self._text(e, 'code'),
                "definition_reference": self.get_defenition_ref(e),
                'role': self._get_attr(e, 'role', 'ref')
            })
    
        return result
    
    def _parse_feature_association(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            
            result.append({
                'is_abstract': self._get_attr(element, 'S100_FC_FeatureAssociation', 'isAbstract'),
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                'code': self._text(e, 'code'),
                "definition_reference": self.get_defenition_ref(e),
                'role': [attr.attrib.get('ref') for attr in self._findall(e, 'role')]
            })
            
        return result
    
    def _parse_info_type(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            
            result.append({
                'is_abstract': self._get_attr(element, 'S100_FC_InformationType', 'isAbstract'),
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                "definition_reference": self.get_defenition_ref(e),
                'attribute_binding': self.get_attr_binding(e)
            })
            
        return result
    
    
    def _parse_feature_type(self, element: Element) -> list[dict]:
        result = []
        
        for e in element:
            
            result.append({
                'name': self._text(e, 'name'),
                'definition': self._text(e, 'definition'),
                'code': self._text(e, 'code'),
                'permitted_primitives': [primitive.text for primitive in self._findall(e, 'permittedPrimitives')],
                "definition_reference": self.get_defenition_ref(e),
                'information_binding': self.get_info_binding(e),
                'feature_binding': self.get_feature_binding(e),
                'feature_use_type': self._text(e, 'featureUseType'),
                'attr_binding': self.get_sub_attr_binding(e, 'attributeBinding'),
            })
            
        return result
            
    ###################################################################################
    
    def get_defenition_ref(self, e: Element) -> dict | None:
        def_ref_group = self._find(e,'definitionReference')
        
        return {
            'scr_identifier': self._text(def_ref_group, 'sourceIdentifier'),
            'definition_ref': self._get_attr(def_ref_group, 'definitionSource', 'ref')
            } if def_ref_group is not None else None
            
            
    def get_multiplicity(self, e: Element) -> dict | None:
        multiplicity_group = self._find(e, 'multiplicity')
        
        return {
            "lower": self._text(multiplicity_group, 'lower'),
            'upper': {
                'xsi:nil': self._get_attr(multiplicity_group, 'upper', f'{_XSI}nil'),
                'infinite': self._get_attr(multiplicity_group, 'upper', 'infinite'),
                'value': self._text(multiplicity_group, 'upper')
                } if multiplicity_group is not None else None
        }
            
    def get_attr_binding(self, e: Element) -> list[dict]:
        result = []
        attrs_group = self._findall(e, 'attributeBinding')
        
        for attr in attrs_group:
           
            result.append({
                'multiplicity': self.get_multiplicity(attr),
                'attribute': self._get_attr(attr, 'attribute', 'ref'),
            })
            
        return result

    def get_sub_attr_binding(self, e: Element, name) -> dict:
        result = []
        
        sub_attrs_group = self._findall(e, name)
        
        for sub_attr in sub_attrs_group:
            permited_vals = self._find(sub_attr, 'permittedValues')
            
            result.append({
                'sequential': self._get_attr(e, 'subAttributeBinding', 'sequential'),
                'attribute': self._get_attr(sub_attr, 'attribute', 'ref'),
                'multiplicity': self.get_multiplicity(sub_attr),
                'permitted_values': [permited_val.text for permited_val in permited_vals] if permited_vals is not None else [],
                'attribute_visibility': self._text(sub_attr, 'attributeVisibility')
            })
             
        return result
    
    
    def get_info_binding(self, e: Element):
        info_binding = self._find(e, 'informationBinding')

        if info_binding is None: return None
        
        return {
            'role_type': self._get_attr(e, 'informationBinding', 'roleType'),
            'multiplicity': self.get_multiplicity(info_binding),
            'association': self._get_attr(info_binding, 'association', 'ref'),
            'role': self._get_attr(info_binding, 'role', 'ref'),
            'feature_type': self._get_attr(info_binding, 'featureType', 'ref')
        }
    
    def get_feature_binding(self, e: Element):
        feature_binding = self._find(e, 'featureBinding')
        
        if feature_binding is None: return None
        
        return {
            'role_type': self._get_attr(e, 'featureBinding', 'roleType'),
            'multiplicity': self.get_multiplicity(feature_binding),
            'association': self._get_attr(feature_binding, 'association', 'ref'),
            'role': self._get_attr(feature_binding, 'role', 'ref'),
            'feature_type': self._get_attr(feature_binding, 'featureType', 'ref')
        }

        
if __name__ == '__main__':
    xmlreader = XMLReaderFeature('source/xml/101_Feature_Catalogue_2.0.0.xml')
    xmlreader.get_info()