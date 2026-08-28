## 📂 Directory Structure

Here is a visual representation of the source code structure:

```text
src/
├── app/               # Web application (Flask), UI, and Jinja templates
├── parsers/           # Lua and XML parsing scripts (S-100 / IHO standards)
└── utils/             # Shared utilities (logger, JSON formatters)
```

### 1. 🌐 `app/`
Contains the core web application and user interface.
* Houses the backend routing logic (e.g., Flask routes).
* Contains the HTML templates and frontend assets used to render the interface (such as the parameter editing fields and preview pages).
* Manages the interaction between the parsed backend data and the end-user.
    * *For deeper technical details, see the [Parsers README](./app/README.md).*

### 2. 🗂️ `parsers/`
The data extraction and transformation engine.
* Contains scripts to read and interpret **Lua** rendering rules and **XML** catalog files (Feature and Portrayal Catalogs).
* Converts complex maritime standard data (S-100 / IHO) into structured **JSON** files.
* *For deeper technical details, see the [Parsers README](./parsers/README.md).*

### 3. 🛠️ `utils/`
Shared utilities and helper functions used across the entire project.
* Contains the **logger** configuration integrated with the web server.
* Includes JSON formatting and data serialization helpers.
* *For usage examples, see the [Utils README](./utils/README.md).*
