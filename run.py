# run.py

from pathlib import Path
import build_data
from src.utils.logger import config_logger, set_flask_logger

LOGGER = config_logger(__name__)
set_flask_logger(LOGGER)

DATA_PATH = Path('data')
if not DATA_PATH.exists() or not DATA_PATH.is_dir():
    build_data.process_data()

from src.app.routes import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)