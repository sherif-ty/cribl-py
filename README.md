# Cribl Edge Installer (Manual Bootstrap)

This script automates the full setup of Cribl Edge on a Linux server and registers it with a Cribl Stream Leader.


## What It Does

- Checks connectivity to Cribl Stream Leader (IP + Port)
- Ensures TCP port (default: 4200) is reachable
- Downloads and installs Cribl Edge
- Creates a dedicated `cribl` system user
- Bootstraps Edge to the leader using a secure token
- Configures systemd service for auto-start
- Starts and enables Cribl Edge


## Folder Structure

cribl_edge_installer/
├── install_cribl_edge.py     # Main installer script
├── README.md                 # You're reading it
├── requirements.txt          # Python dependencies (currently empty)
└── run.sh                    # Optional shell wrapper

## Requirements

- Python 3.x
- `sudo` access
- Internet access (for downloading Cribl Edge)
- port 4200 open in the Edge machine


## Python Dependencies

Install them via:

pip install -r requirements.txt

## Running the Script
option1: run the python file
sudo python3 install_cribl_edge.py
option2: run the shell file
chmod +x run.sh
./run.sh
