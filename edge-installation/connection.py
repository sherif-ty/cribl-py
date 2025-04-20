import os
import platform
import subprocess
import socket
import urllib.parse
import sys

# ----------------------------
# Configuration
# ----------------------------

CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"
INSTALL_DIR = "/opt/cribl"
LEADER_IP = "3.123.253.64"
LEADER_PORT = 9000
EDGE_TOKEN = "eOHdmkvEJsN3QQvDz8T7tkQpV9SnYEqZ"
FLEET_NAME = "default_fleet"

# ----------------------------
# Utilities
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
# Installer Steps
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

def install_edge_via_curl():
    print("Registering Cribl Edge using install-edge.sh from the Leader")
    encoded_dir = urllib.parse.quote(INSTALL_DIR)
    url = f"http://{LEADER_IP}:{LEADER_PORT}/init/install-edge.sh" \
          f"?group={FLEET_NAME}&token={EDGE_TOKEN}" \
          f"&user={CRIBL_USER}&user_group={CRIBL_GROUP}&install_dir={encoded_dir}"

    full_command = f"curl '{url}' | bash -"
    run(full_command)

# ----------------------------
# Main
# ----------------------------

def main():
    try:
        check_connectivity()
        create_user_group()
        set_permissions()
        install_edge_via_curl()
        print("\nCribl Edge registration completed.")
    except Exception as e:
        print(f"\nInstallation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
