import os

from flask import Flask

from ..data_manager import get_svg
from .main import main_bp
from .features import features_bp
from .attributes import attributes_bp
from .symbols import symbols_bp
from .rules import rules_bp


def create_app():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')
    
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
    
    app.jinja_env.globals['get_svg'] = get_svg
    
    app.register_blueprint(main_bp)
    app.register_blueprint(features_bp)
    app.register_blueprint(attributes_bp)
    app.register_blueprint(symbols_bp)
    app.register_blueprint(rules_bp)
    
    return app