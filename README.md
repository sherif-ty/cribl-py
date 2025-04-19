
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
- **Creates and joins a Fleet** (new functionality)

## Folder Structure
```sh
cribl_edge_installer/
├── install_cribl_edge.py     # Main installer script
├── config.txt                # Configuration file
├── README.md                 # You're reading it
├── requirements.txt          # Python dependencies
└── run.sh                    # Optional shell wrapper
```

## Requirements

- Python 3.x
- `sudo` access
- Internet access (for downloading Cribl Edge)
- port 4200 open in the Edge machine

## Configuration File

Create a `config.txt` file with the following content:
```sh
CRIBL_USER=cribl
CRIBL_GROUP=cribl
EDGE_NAME=edge-server2
LEADER_IP=10.0.0.1
LEADER_PORT=4200
CRIBL_VERSION=4.5.2
CRIBL_DIR=/opt/cribl
TOKEN=your-token-from-stream-ui
FLEET_NAME=my-fleet
```

## Python Dependencies

Install them via:
```sh
# Option 1: Run the Python file
pip install -r requirements.txt
sudo python3 install_cribl_edge.py

# Option 2: Run the shell file
chmod +x run.sh
./run.sh
```

### NOTE ###
If you don't want to create a fleet, you can simply remove or comment out the create_fleet() and join_fleet() function calls in the main() function. Here's the modified main() function
```sh
def main():
    if not check_connectivity(LEADER_IP, LEADER_PORT):
        sys.exit(1)
    
    create_user(CRIBL_USER, CRIBL_GROUP)
    download_and_extract_tarball()
    set_permissions(CRIBL_DIR, CRIBL_USER, CRIBL_GROUP)
    # create_fleet()  # Commented out
    bootstrap_edge()
    # join_fleet()  # Commented out
    enable_systemd()
    start_cribl()
    print(f"\n Cribl Edge installed and connected to Leader at {LEADER_URL}")
```