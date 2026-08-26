# Analyseur S-101

**A web application designed to visualize the International Hydrographic Organization (IHO) S-101 norme for standard for Eletronic Navigational Charts (ENCs)**

## ⚙️ Prerequisites & Installation

Ensure you have **Python 3** installed on your system. It is highly recommended to use a virtual environment (`.venv`).

1. Clone the repository and navigate to project folder:

```bash
git clone https://github.com/Jibede/S100PSexplorer.git
cd S100PSexplorer
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 🛠️ Usage

Running the application requires a simple two-step process:

- Building the data context
- Starting the server

1. Data Preparation

Run the build script to parse the catalogues and generate the necessary data structures.

```bash
python build_data.py
```

2. Start the Application

Lauch the Flask web server.

```bash
python run.py
```

3. Access the Application

Once the server is running, open your web browser and navigate to:

```plaintext
http://localhost:5000
```
