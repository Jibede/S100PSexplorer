# 🛠️ Utils Module (`src/utils/`)

This directory contains shared utility functions and helper scripts used across the application. These tools provide consistent behavior for cross-cutting concerns, such as application logging and data serialization, ensuring that all modules communicate and report errors uniformly.

---

## 📂 Structure and Components

### `logger.py`
The centralized logging configuration for the entire project. It replaces standard print statements with a robust, color-coded logging system.

* **Main Features:**
  * **Color-Coded Output:** Uses ANSI escape codes to automatically colorize terminal logs based on their severity level (e.g., Red for `ERROR` and `CRITICAL`, Yellow for `WARNING`, Gray for `DEBUG`).
  * **Custom Formatting:** Standardizes the log output to include critical debugging context:
    `[LEVEL] (filename:lineno) (YYYY/MM/DD HH:MM:SS): message`
  * **Flask Server Integration (`set_flask_logger`):** Overrides the default `werkzeug` logger used by Flask web servers. This ensures that HTTP request logs follow the same visual format and color scheme as the application's internal logs.

### `formatter.py` [ JSON Helpers ]
* Contains simple wrapper functions (like `get_json`) to safely serialize text and Python objects into JSON strings, which is heavily used when preparing data for API responses or file writing.

---

## 🚀 Usage Example

To use the centralized logger in any other module of the project:

```python
from src.utils.logger import config_logger

# Initialize the logger with the current module's name
LOGGER = config_logger(__name__)

LOGGER.debug("This is a debug message (Gray).")
LOGGER.warning("This is a warning message (Yellow).")
LOGGER.error("This is an error message (Red).")
```

If initializing a Flask application, you can unify the logs by passing the configured logger:

```python
from src.utils.logger import config_logger, set_flask_logger
from flask import Flask

app = Flask(__name__)
my_logger = config_logger(__name__)

# Apply the custom logger to the Flask server
set_flask_logger(my_logger)
```
