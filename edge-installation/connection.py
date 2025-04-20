import os
import platform
import subprocess
import tarfile
import urllib.request
import socket
import time
import sys

# ----------------------------
# Configuration
# ----------------------------

CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"
INSTALL_DIR = "/opt/cribl"
LEADER_IP = "3.123.253.64"
LEADER_PORT = 4200
LEADER_PROTOCOL = "http"
EDGE_TOKEN = "eOHdmkvEJsN3QQvDz8T7tkQpV9SnYEqZ"
FLEET_NAME = "default_fleet"
CRIBL_TARBALL_PATH = "/tmp/cribl-edge.tgz"

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
# Installer Steps
# ----------------------------

def check_connectivity():
    print(f"Step 1: Checking connectivity to {LEADER_IP}:{LEADER_PORT}")
    try:
        with socket.create_connection((LEADER_IP, LEADER_PORT), timeout=5):
            print("Cribl Leader is reachable.")
    except Exception as e:
        raise RuntimeError(f"Unable to connect to Cribl Leader at {LEADER_IP}:{LEADER_PORT}: {e}")

def detect_architecture():
    arch = platform.machine()
    if arch == "x86_64":
        return "latest-x64"
    elif arch == "aarch64":
        return "latest-arm64"
    else:
        raise ValueError(f"Unsupported architecture: {arch}")

def download_cribl():
    print("Step 2: Downloading Cribl Edge")
    try:
        arch_path = detect_architecture()
        url = f"https://cdn.cribl.io/dl/{arch_path}"
        print(f"Fetching version URL from: {url}")
        tarball_url = urllib.request.urlopen(url).read().decode().strip()
        print(f"Downloading tarball from: {tarball_url}")
        urllib.request.urlretrieve(tarball_url, CRIBL_TARBALL_PATH)
        print(f"Cribl Edge downloaded to: {CRIBL_TARBALL_PATH}")
    except Exception as e:
        raise RuntimeError(f"Failed to download Cribl Edge: {e}")

def extract_tarball():
    print("Step 3: Extracting Cribl Edge")
    try:
        with tarfile.open(CRIBL_TARBALL_PATH, "r:gz") as tar:
            tar.extractall(path="/opt")
        print(f"Cribl Edge extracted to {INSTALL_DIR}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract Cribl Edge tarball: {e}")

def create_user_group():
    print("Step 4: Creating cribl system user and group")
    try:
        run(f"id -u {CRIBL_USER} || sudo useradd -m -s /bin/bash {CRIBL_USER}", check=False)
        run(f"getent group {CRIBL_GROUP} || sudo groupadd {CRIBL_GROUP}", check=False)
        run(f"sudo usermod -aG {CRIBL_GROUP} {CRIBL_USER}", check=False)
        print("User and group setup complete.")
    except Exception as e:
        raise RuntimeError(f"Failed to create cribl user or group: {e}")

def set_permissions():
    print("Step 5: Setting directory permissions")
    try:
        run(f"sudo chown -R {CRIBL_USER}:{CRIBL_GROUP} {INSTALL_DIR}")
        print("Permissions applied.")
    except Exception as e:
        raise RuntimeError(f"Failed to set directory permissions: {e}")

def bootstrap_edge():
    print("Step 6: Bootstrapping Cribl Edge with the Leader")
    try:
        run(f"sudo -u {CRIBL_USER} {INSTALL_DIR}/bin/cribl mode-edge "
            f"-H {LEADER_IP} -p {LEADER_PORT} --token {EDGE_TOKEN} --group {FLEET_NAME}")
        print("Edge bootstrapped successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to bootstrap Cribl Edge: {e}")

def enable_systemd():
    print("Step 7: Enabling systemd service for Cribl Edge")
    try:
        run(f"sudo {INSTALL_DIR}/bin/cribl boot-start enable -m systemd -u {CRIBL_USER}", check=False)
        print("Systemd service enabled.")
    except Exception as e:
        raise RuntimeError(f"Failed to enable Cribl Edge systemd service: {e}")

def start_cribl():
    print("Step 8: Starting Cribl Edge service")
    try:
        run("sudo systemctl daemon-reexec", check=False)
        run("sudo systemctl enable cribl", check=False)
        run("sudo systemctl start cribl")
        time.sleep(2)
        run("sudo systemctl status cribl", check=False)
        print("Cribl Edge service is now running.")
    except Exception as e:
        raise RuntimeError(f"Failed to start Cribl Edge service: {e}")

# ----------------------------
# Main
# ----------------------------

def main():
    try:
        check_connectivity()
        download_cribl()
        extract_tarball()
        create_user_group()
        set_permissions()
        bootstrap_edge()
        enable_systemd()
        start_cribl()
        print("\nCribl Edge installation completed successfully.")
    except Exception as error:
        print(f"\nInstallation failed: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
