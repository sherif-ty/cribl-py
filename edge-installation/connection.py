import requests
import sys
import os

# Configuration variables
CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"
EDGE_NAME = "python-edge"
LEADER_IP = "3.123.253.64"
LEADER_PORT = 4200
CRIBL_VERSION = "4.5.2"
CRIBL_DIR = "/opt/cribl"
TOKEN = "criblmaster"
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
    os.system(f"sudo useradd -m -s /bin/bash {user}")
    os.system(f"sudo groupadd {group}")
    os.system(f"sudo usermod -aG {group} {user}")

def download_and_extract_tarball():
    url = f"https://cdn.cribl.io/dl/cribl-{CRIBL_VERSION}-linux-x64.tgz"
    os.system(f"wget {url} -O /tmp/cribl.tgz")
    os.system(f"sudo tar -xzf /tmp/cribl.tgz -C {CRIBL_DIR}")

def set_permissions(directory, user, group):
    os.system(f"sudo chown -R {user}:{group} {directory}")

def bootstrap_edge():
    os.system(f"sudo -u {CRIBL_USER} {CRIBL_DIR}/bin/cribl edge bootstrap --token {TOKEN} --leader {LEADER_URL}")

def enable_systemd():
    os.system("sudo systemctl enable cribl")

def start_cribl():
    os.system("sudo systemctl start cribl")

def main():
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
