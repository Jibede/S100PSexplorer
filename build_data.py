# build_data.py
from pathlib import Path

from src.parsers.LuaInterpreter import LuaInterpreter
from src.parsers.XMLReaderAditionalFiles import XMLReaderAditionalFiles
from src.parsers.XMLReaderFeature import XMLReaderFeature
from src.parsers.XMLReaderPortrayal import XMLReaderPortrayal
from src.utils.logger import config_logger

RAW_DATA_PATH = Path('raw')

LUA_RULES = RAW_DATA_PATH / 'rules' / '*.lua'
PORTRAYAL_PATH = RAW_DATA_PATH / 'xml' / 'portrayal_catalogue.xml'
FEATURE_PATH = RAW_DATA_PATH / 'xml' / '101_Feature_Catalogue_2.0.0.xml'
LINE_STYLES_PATH = RAW_DATA_PATH / 'lineStyles' / '*.xml'
AREA_FILLS_PATH = RAW_DATA_PATH / 'areaFills' / '*.xml'
COLOR_PROFILES_PATH = RAW_DATA_PATH / 'colorProfiles' / '*.xml'


LOGGER = config_logger(__name__)
def process_data(file_name: str = None):
    CHECK_1 = 'portrayal_catalogue'
    CHECK_2 = 'feature_catalogue'
    
    LOGGER.info('STARTING THE EXTRACTION AND PROCESSING OF THE FILES ...')
    
    if  file_name is None or CHECK_1 in file_name.lower():
        
        LOGGER.info(f'RUNNING {CHECK_1.upper()} PARSERS !!!')
        
        lua_interpreter = LuaInterpreter(LUA_RULES)
        xml_reader_portrayal = XMLReaderPortrayal(PORTRAYAL_PATH)
        xml_reader_aditional = XMLReaderAditionalFiles()
        
        lua_interpreter.get_analyses()
        xml_reader_portrayal.get_info()
        xml_reader_aditional.get_info(LINE_STYLES_PATH)
        xml_reader_aditional.get_info(AREA_FILLS_PATH)
        xml_reader_aditional.get_info(COLOR_PROFILES_PATH)
        
    if  file_name is None or CHECK_2 in file_name.lower():
        
        LOGGER.info(f'RUNNING {CHECK_2.upper()} PARSERS !!!')
        
        xml_reader_feature = XMLReaderFeature(FEATURE_PATH)
        xml_reader_feature.get_info()
    

    LOGGER.info('PROCESSING COMPLETE ! JSONs SUCCESSFULLY GENERATED.')
    
if __name__ == '__main__':
    process_data()