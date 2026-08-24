# src/routes/__init__.py
import os

from flask import Flask

from ..data_manager import set_variations, extract_svg_data, get_svg, get_svg_color, transform_mm_px
from .main import main_bp
from .features import features_bp
from .attributes import attributes_bp
from .visualisation import visualisation_bp
from .rules import rules_bp
from .text_group import text_group_bp
from .colors import colors_bp
from .save_file import save_file_bp


def create_app():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, '..', 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')
    
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
    
    # Global enviroment functions
    app.jinja_env.globals['get_svg'] = get_svg
    app.jinja_env.globals['transform_mm_px'] = transform_mm_px
    app.jinja_env.globals['extract_svg_data'] = extract_svg_data
    app.jinja_env.globals['get_svg_color'] = get_svg_color
    app.jinja_env.globals['get_multi'] = set_variations

    
    # Routes
    app.register_blueprint(main_bp)
    app.register_blueprint(features_bp)
    app.register_blueprint(attributes_bp)
    app.register_blueprint(visualisation_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(text_group_bp)
    app.register_blueprint(colors_bp)
    app.register_blueprint(save_file_bp)
    
    return app