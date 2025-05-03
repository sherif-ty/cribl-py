import os
import platform
import subprocess
import socket
import urllib.parse
import sys

# ----------------------------
# Config Loader
# ----------------------------

def load_config(file_path):
    config = {}
    with open(file_path) as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

# ----------------------------
# Load Config
# ----------------------------

config = load_config("config.txt")

ENVIRONMENT = config["ENVIRONMENT"]
CRIBL_USER = config["CRIBL_USER"]
CRIBL_GROUP = config["CRIBL_GROUP"]
INSTALL_DIR = config["INSTALL_DIR"]
LEADER_IP = config["LEADER_IP"]
LEADER_PORT = int(config["LEADER_PORT"])
EDGE_TOKEN = config["EDGE_TOKEN"]
FLEET_NAME = config["FLEET_NAME"]
CRIBL_VERSION = config["CRIBL_VERSION"]

# ----------------------------
# Utility
# ----------------------------

def run(command, check=True):
    print(f"\nRunning: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}")

# ----------------------------
# Linux Installation Steps
# ----------------------------

def check_connectivity():
    print(f"Checking connectivity to {LEADER_IP}:{LEADER_PORT}")
    try:
        with socket.create_connection((LEADER_IP, LEADER_PORT), timeout=5):
            print("Cribl Leader is reachable.")
    except Exception as e:
        raise RuntimeError(f"Could not connect to Cribl Leader at {LEADER_IP}:{LEADER_PORT}: {e}")

def create_user_group():
    print("Creating cribl system user and group if they don't exist")
    run(f"id -u {CRIBL_USER} || sudo useradd -m -s /bin/bash {CRIBL_USER}", check=False)
    run(f"getent group {CRIBL_GROUP} || sudo groupadd {CRIBL_GROUP}", check=False)
    run(f"sudo usermod -aG {CRIBL_GROUP} {CRIBL_USER}", check=False)

def set_permissions():
    print("Ensuring permissions on installation directory")
    run(f"sudo mkdir -p {INSTALL_DIR}")
    run(f"sudo chown -R {CRIBL_USER}:{CRIBL_GROUP} {INSTALL_DIR}")

def restart_and_verify_service():
    print("Restarting Cribl Edge service")
    run("sudo systemctl restart cribl")
    run("sudo systemctl status cribl", check=False)

def install_linux():
    check_connectivity()
    create_user_group()
    set_permissions()

    print("Installing Cribl Edge using the install-edge.sh script")
    encoded_dir = urllib.parse.quote(INSTALL_DIR)
    url = f"http://{LEADER_IP}:{LEADER_PORT}/init/install-edge.sh" \
          f"?group={FLEET_NAME}&token={EDGE_TOKEN}" \
          f"&user={CRIBL_USER}&user_group={CRIBL_GROUP}&install_dir={encoded_dir}"
    run(f"curl '{url}' | bash -")

    restart_and_verify_service()
    print("Cribl Edge for Linux installed and started.")

# ----------------------------
# Other Environments
# ---------------------------

def install_windows():
    print("Windows installation command:")
    
    # Load configuration values
    config = load_config("config.txt")
    FOR_WINDOWS_CRIBL_PKG_URL = config["For_Windows_cribl_pkg_url"]
    LEADER_IP = config["LEADER_IP"]
    EDGE_TOKEN = config["EDGE_TOKEN"]
    FLEET_NAME = config["FLEET_NAME"]
    
    # Construct the msiexec command using values from the config file
    command = f'msiexec /i "{FOR_WINDOWS_CRIBL_PKG_URL}" /qn MODE=mode-managed-edge HOSTNAME={LEADER_IP} PORT=4200 AUTH={EDGE_TOKEN} FLEET={FLEET_NAME}'
    
    if platform.system() == "Windows":
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Return code: {result.returncode}")
        print(f"Standard output: {result.stdout}")
        print(f"Standard error: {result.stderr}")
        
        if result.returncode == 0:
            # Restart the Cribl service
            run("net stop cribl")
            run("net start cribl")
            print("Installation done successfully.")
        else:
            raise RuntimeError(f"Installation failed with return code {result.returncode}")
    else:
        print("This script must be run in a Windows environment.")

        
def install_docker():
    print("Docker installation command:")
    command = (
        f"docker run -d --privileged "
        f"-e \"CRIBL_DIST_MASTER_URL=tcp://{EDGE_TOKEN}@{LEADER_IP}:4200?group={FLEET_NAME}\" "
        f"-e \"CRIBL_DIST_MODE=managed-edge\" "
        f"-e \"CRIBL_EDGE=1\" "
        f"-p 9420:9420 "
        f"-v \"/:/hostfs:ro\" "
        f"--restart unless-stopped "
        f"--name \"cribl-edge\" "
        f"cribl/cribl:{CRIBL_VERSION}"
    )
    print(command)

def install_kubernetes():
    print("Kubernetes Helm command:")
    command = (
        f"helm install --repo \"https://criblio.github.io/helm-charts/\" "
        f"--version \"^{CRIBL_VERSION}\" --create-namespace "
        f"-n \"cribl\" --set \"cribl.leader=tcp://{EDGE_TOKEN}@{LEADER_IP}?group={FLEET_NAME}\" "
        f"\"cribl-edge\" edge"
    )
    print(command)

# ----------------------------
# Main
# ----------------------------

def main():
    try:
        if ENVIRONMENT == "linux":
            install_linux()
        elif ENVIRONMENT == "windows":
            install_windows()
        elif ENVIRONMENT == "docker":
            install_docker()
        elif ENVIRONMENT == "kubernetes":
            install_kubernetes()
        else:
            raise ValueError(f"Unsupported environment: {ENVIRONMENT}")
    except Exception as error:
        print(f"\nInstallation failed: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
