# build_data.py
from src.parsers.LuaInterpreter import LuaInterpreter
from src.parsers.XMLReaderAditionalFiles import XMLReaderAditionalFiles
from src.parsers.XMLReaderFeature import XMLReaderFeature
from src.parsers.XMLReaderPortrayal import XMLReaderPortrayal
from src.utils.logger import config_logger

LOGGER = config_logger(__name__)
def process_data():
    LOGGER.info('STARTING THE EXTRACTION AND PROCESSING OF THE FILES ...')
    
    lua_interpreter = LuaInterpreter('source/rules/*.lua')
    xml_reader_adtional = XMLReaderAditionalFiles()
    xml_reader_feature = XMLReaderFeature('source/xml/101_Feature_Catalogue_2.0.0.xml')
    xml_reader_portrayal = XMLReaderPortrayal('source/xml/portrayal_catalogue.xml')
    
    lua_interpreter.get_analyses()
    xml_reader_feature.get_info()
    xml_reader_portrayal.get_info()
    xml_reader_adtional.get_info('source/lineStyles/*.xml')
    xml_reader_adtional.get_info('source/areaFills/*.xml')
    xml_reader_adtional.get_info('source/colorProfiles/*.xml')

    LOGGER.info('PROCESSING COMPLETE ! JSONs SUCCESSFULLY GENERATED.')