from src.parsers.LuaInterpreter import LuaInterpreter
from src.parsers.XMLReaderAditionalFiles import XMLReaderAditionalFiles
from src.parsers.XMLReaderFeature import XMLReaderFeature
from src.parsers.XMLReaderPortrayal import XMLReaderPortrayal
from src.utils import logger

# from src.app.routes import create_app

LOGGER = logger.config_logger(__name__)

lua_interpreter = LuaInterpreter('source/rules/*.lua')
xml_reader_adtional = XMLReaderAditionalFiles()
xml_reader_feature = XMLReaderFeature('source/xml/101_Feature_Catalogue_2.0.0.xml')
xml_reader_portrayal = XMLReaderPortrayal('source/xml/portrayal_catalogue.xml')

# app = create_app()


if __name__ == '__main__':
    
    lua_interpreter.get_json_analyses()
    
    xml_reader_adtional.get_info('source/lineStyles/*.xml')
    xml_reader_adtional.get_info('source/areaFills/*.xml')
    xml_reader_adtional.get_info('source/colorProfiles/*.xml')
    
    xml_reader_feature.get_info()
    
    xml_reader_portrayal.get_info()
    
    # app.run(debug=True, port=5000)