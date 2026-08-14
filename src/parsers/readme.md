# 🗂️ Parsers Module (`src/parsers/`)

This directory contains the scripts responsible for parsing (reading, interpreting, and converting) files related to maritime catalogs and rendering rules (such as those based on the **S-100 / IHO** standard). 

The main goal of these parsers is to process structured files in **XML** format and **Lua** scripts, extract their information, and convert them into structured **JSON** files so they can be easily consumed and manipulated by the rest of the system or frontend.

---

## 📂 Structure and Components

The module consists of four main classes, each responsible for a specific data domain:

### 1. `LuaInterpreter.py` (Lua Rules Interpreter)
Responsible for analyzing the rendering rules files (Portrayal Rules) written in Lua.
* **How it works:** Uses the `luaparser` library to read Lua code and transform it into an Abstract Syntax Tree (AST).
* **Main Features:**
  * Navigates the AST to identify variables, conditionals (`if/elseif/else`), and function calls.
  * Extracts drawing instructions (*PointInstruction*, *LineInstruction*, *AreaFillReference*, etc.).
  * Resolves logic and display negations of components on the map.
  * Generates relationship JSON files detailing where each symbol, color, or viewing group is used (`related_symbols.json`, `related_colors.json`, `related_vw.json`).

### 2. `XMLReaderFeature.py` (Feature Catalog Reader)
Responsible for reading and processing the Feature Catalog XML files.
* **Main Features:**
  * Parses `S100_FC_*` tags.
  * Extracts simple and complex attributes (`SimpleAttributes`, `ComplexAttributes`).
  * Maps Information Types (`InformationTypes`) and Feature Types (`FeatureTypes`).
  * Associates relationships, bindings, and multiplicities of features.

### 3. `XMLReaderPortrayal.py` (Portrayal Catalog Reader)
Responsible for extracting metadata from the Portrayal Catalog.
* **Main Features:**
  * Reads the root structure of visual catalogs.
  * Maps simple groups (*colorProfiles*, *symbols*, *styleSheets*, *lineStyles*, etc.).
  * Extracts alert catalogs, viewing groups (`viewingGroups`), layers, and display planes (`displayPlanes`).

### 4. `XMLReaderAditionalFiles.py` (Style Files Reader)
Focused on parsing accessory XML files that detail the visual styles of components on the map.
* **Main Features:**
  * Processes color profiles (`colorProfiles`), creating a dictionary with tokens and RGB codes for day, night, or dusk modes.
  * Extracts complex line styles (`lineStyles`), including thicknesses, dash lengths, and embedded symbols.
  * Processes area fill patterns (`areaFills`).

---

## ⚙️ Data Flow (Input / Output)

* **Inputs:** Raw files located in project directories with `.lua` or `.xml` extensions.
* **Outputs:** Data is processed and serialized into the `./data/` folder, organized into subdirectories according to the class:
  * `./data/rules_parsed/` (Conditions and metadata read from Lua)
  * `./data/featureCatalog/` (Features mapped in JSON)
  * `./data/portrayalCatalog/` (Visuals mapped in JSON)
  * `./data/aditionalFiles/` (Lines, Colors, and Areas)
  * `./data/related_*.json` (General relationships)

---

## 🛠️ Technologies and Libraries

* `xml.etree.ElementTree`: Used for parsing and structured navigation through XML document trees.
* `luaparser`: Library to read Lua files and generate the Abstract Syntax Tree (AST).
* `json` & `pathlib`: File system manipulation, formatting outputs, and exporting objects.