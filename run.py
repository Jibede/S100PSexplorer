from src.utils.logger import config_logger, set_flask_logger
from src.app.routes import create_app

LOGGER = config_logger(__name__)
set_flask_logger(LOGGER)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)