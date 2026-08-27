# 🗂️ App Module - Web Application (`src/app/`)

This directory contains the core web application. It manages the routing, data handling, and user interface for exploring and visualizing marine chart features, attributes, and portrayal rules.

## 📂 Directory Structure

```text
.
├── data_manager.py      # Core data management logic
│
├── routes/              # Application endpoints
│   ├── __init__.py      # Route aggregation and initialization
│   ├── attributes.py    # Route for inspecting chart attributes
│   ├── colors.py        # Route for color profiles
│   ├── features.py      # Route for feature definitions
│   ├── main.py          # Main application entry point/index
│   ├── rules.py         # Route for viewing and editing portrayal rules
│   ├── save_file.py     # Route for handling file save operations
│   ├── text_group.py    # Route for text group management
│   └── visualisation.py # Route for the canvas visualization engine
│
├── static/              # Frontend assets
│   ├── css/             # Stylesheets (including day/dusk/night themes)
│   ├── js/              # Client-side scripts (canvas_renderer.js, UI updates)
│   └── symbols/         # Extensive library of SVG nautical symbols
│         
└── templates/           # Jinja2 HTML templates
    ├── _components.html # Reusable UI components
    ├── _draw_img.html   # Image drawing partials
    ├── attributes/      # Templates for attributes UI
    ├── base/            # Base layouts (navbar, sidebar)
    ├── colors/          # Templates for colors UI
    ├── features/        # Templates for features UI
    ├── rules/           # Templates for rules editor UI
    ├── text_groups/     # Templates for text groups UI
    └── visualisation/   # Templates for the visualizer UI
```

## 🛠️ Technology Stack

- **Backend:** Python (Modular routing system)
- **Frontend:** HTML, CSS, JavaScript (Dynamic UI and Canvas Renderer)
- **Templating:** HTML templates with a component-based architecture (e.g., Jinja2)

## 🚀 Core Components

- **Data Management:** `data_manager.py` handles the state and data flow between the parsed catalog and the frontend.

