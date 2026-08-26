# build_data.py
from src.parsers.LuaInterpreter import LuaInterpreter
from src.parsers.XMLReaderAditionalFiles import XMLReaderAditionalFiles
from src.parsers.XMLReaderFeature import XMLReaderFeature
from src.parsers.XMLReaderPortrayal import XMLReaderPortrayal
from src.utils.logger import config_logger

LOGGER = config_logger(__name__)
def process_data(file_name: str = None):
    check_1 = 'portrayal_catalogue'
    check_2 = 'feature_catalogue'
    
    LOGGER.info('STARTING THE EXTRACTION AND PROCESSING OF THE FILES ...')
    
    if  file_name is None or check_1 in file_name.lower():
        
        LOGGER.info(f'RUNNING {check_1.upper()} PARSERS !!!')
        
        lua_interpreter = LuaInterpreter('source/rules/*.lua')
        xml_reader_portrayal = XMLReaderPortrayal('source/xml/portrayal_catalogue.xml')
        xml_reader_aditional = XMLReaderAditionalFiles()
        
        lua_interpreter.get_analyses()
        xml_reader_portrayal.get_info()
        xml_reader_aditional.get_info('source/lineStyles/*.xml')
        xml_reader_aditional.get_info('source/areaFills/*.xml')
        xml_reader_aditional.get_info('source/colorProfiles/*.xml')
        
    if  file_name is None or check_2 in file_name.lower():
        
        LOGGER.info(f'RUNNING {check_2.upper()} PARSERS !!!')
        
        xml_reader_feature = XMLReaderFeature('source/xml/101_Feature_Catalogue_2.0.0.xml')
        xml_reader_feature.get_info()
    

    LOGGER.info('PROCESSING COMPLETE ! JSONs SUCCESSFULLY GENERATED.')
    
if __name__ == '__main__':
    process_data()