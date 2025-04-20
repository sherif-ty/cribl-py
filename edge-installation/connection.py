import requests
import sys
import os
import platform
import subprocess

# Configuration variables
CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"
EDGE_NAME = "python-edge"
LEADER_IP = "3.123.253.64"
LEADER_PORT = 4200
CRIBL_VERSION = "latest"
CRIBL_DIR = "/opt/cribl"
TOKEN = "eOHdmkvEJsN3QQvDz8T7tkQpV9SnYEqZ"
FLEET_NAME = "python-fleet"
LEADER_PROTOCOL = "http"

def check_connectivity(ip, port):
    try:
        response = requests.get(f"http://{ip}:{port}")
        return response.status_code == 200
    except requests.ConnectionError:
        print(f"Could not connect to {ip}:{port}")
        return False

def detect_leader_protocol(protocol, ip, port):
    url = f"{protocol}://{ip}:{port}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return url
        else:
            raise Exception(f"Could not connect to Cribl Leader using {protocol}")
    except requests.ConnectionError:
        raise Exception(f"Could not connect to Cribl Leader using {protocol}")

def create_user(user, group):
    if os.system(f"id -u {user}") != 0:
        os.system(f"sudo useradd -m -s /bin/bash {user}")
    if os.system(f"getent group {group}") != 0:
        os.system(f"sudo groupadd {group}")
    os.system(f"sudo usermod -aG {group} {user}")

def download_and_extract_tarball():
    arch = platform.machine()
    if arch == "x86_64":
        os.system("curl -Lso - $(curl https://cdn.cribl.io/dl/latest-x64) | sudo tar zxv -C /opt")
    elif arch == "aarch64":
        os.system("curl -Lso - $(curl https://cdn.cribl.io/dl/latest-arm64) | sudo tar zxv -C /opt")
    else:
        print(f"Unsupported architecture: {arch}")
        sys.exit(1)

def set_permissions(directory, user, group):
    os.system(f"sudo chown -R {user}:{group} {directory}")

def bootstrap_edge():
    os.system(f"sudo -u {CRIBL_USER} {CRIBL_DIR}/bin/cribl mode-edge -H {LEADER_IP} -p {LEADER_PORT}")

def enable_systemd():
    process = subprocess.Popen(
        ["sudo", f"{CRIBL_DIR}/bin/cribl", "boot-start", "enable", "-m", "systemd", "-u", CRIBL_USER],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    process.communicate(input=b'y\n')

def start_cribl():
    os.system("sudo systemctl start cribl")

def main():
    global LEADER_URL
    if not check_connectivity(LEADER_IP, LEADER_PORT):
        sys.exit(1)
    
    LEADER_URL = detect_leader_protocol(LEADER_PROTOCOL, LEADER_IP, LEADER_PORT)
    create_user(CRIBL_USER, CRIBL_GROUP)
    download_and_extract_tarball()
    set_permissions(CRIBL_DIR, CRIBL_USER, CRIBL_GROUP)
    bootstrap_edge()
    enable_systemd()
    start_cribl()
    print(f"\n Cribl Edge installed and connected to Leader at {LEADER_URL}")

if __name__ == "__main__":
    main()
