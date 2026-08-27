# Analyzer S-101

**A web application designed to visualize the International Hydrographic Organization (IHO) S-101 standard for Electronic Navigational Charts (ENCs)**

## 📂 Project Structure

```text
S100PSexplorer/
├── raw/                # Data raw Catalogs
├── src/                # Lua and XML parsing scripts and Web application (Flask)
├── build_data.py       # Script to process raw data
├── run.py              # Main entry point to launch the Flask web server
└── requirements.txt    # List of project dependencies and Python packages
```

## ⚙️ Prerequisites & Installation

Ensure you have **Python 3** installed on your system. It is highly recommended to use a virtual environment (`venv`).

1. Clone the repository and navigate to project folder:

```bash
git clone https://github.com/Jibede/S100PSexplorer.git
cd S100PSexplorer
git checkout joao_branch
```

2. Create and enable a virtual envionment (recommend):

* For Windows: 
```bash
python -m venv venv
venv/Scripts/activate
```

* For Linux: 
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 🛠️ Usage

1. Start the Application

* Lauch the Flask web server.

```bash
python run.py
```

2. Access the Application

* Once the server is running, open your web browser and navigate to:

```plaintext
http://localhost:5000
```
