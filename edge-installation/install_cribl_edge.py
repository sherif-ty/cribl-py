import os
import subprocess
import urllib.request
import tarfile
import shutil
import pwd
import grp
import socket
import time
import sys
import json
import requests
import platform

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings()

# ==== Helper: Detect HTTP or HTTPS Protocol ====
def detect_leader_protocol(host, port):
    for protocol in ["https", "http"]:
        try:
            url = f"{protocol}://{host}:{port}/api/v1/version"
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 200:
                print(f"[+] Detected working protocol: {protocol.upper()}")
                return f"{protocol}://{host}:{port}"
        except requests.exceptions.RequestException as e:
            print(f"[!] {protocol.upper()} failed: {e}")
    raise Exception("Could not connect to Cribl Leader using HTTP or HTTPS")

# ==== Read Configuration from File ====
def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and '=' in line:
                name, value = line.split('=', 1)
                config[name] = value
    return config

# Load the configuration from 'config.txt'
config = read_config('config.txt')

# Read values
CRIBL_USER = config['CRIBL_USER']
CRIBL_GROUP = config['CRIBL_GROUP']
EDGE_NAME = config['EDGE_NAME']
LEADER_IP = config['LEADER_IP']
LEADER_PORT = int(config['LEADER_PORT'])
CRIBL_VERSION = config['CRIBL_VERSION']
CRIBL_TARBALL_NAME = config['CRIBL_TARBALL_NAME']
CRIBL_DIR = config['CRIBL_DIR']
TOKEN = config['TOKEN']
FLEET_NAME = config['FLEET_NAME']

# Auto-detect protocol + form leader URL
LEADER_URL = detect_leader_protocol(LEADER_IP, LEADER_PORT)

# ==== Detect System Architecture ====
def detect_architecture():
    arch = platform.machine().lower()
    if "x86_64" in arch:
        return "x64"
    elif "aarch64" in arch:
        return "arm64"
    else:
        raise Exception("Unsupported architecture: " + arch)

# ==== Download and Extract Cribl ====
def download_and_extract_tarball():
    os.makedirs(CRIBL_DIR, exist_ok=True)
    os.chdir("/opt")

    architecture = detect_architecture()
    tarball_url = f"https://cdn.cribl.io/dl/latest-{architecture}"
    print(f"[+] Downloading Cribl Edge for {architecture} architecture from {tarball_url}")
    
    try:
        download_url = subprocess.getoutput(f"curl -s {tarball_url}")
        subprocess.run(f"curl -Lso - {download_url} | tar zxv", shell=True, check=True)
        print("[+] Extracted files:")
        subprocess.run("ls -l", shell=True)
        os.rename(f"cribl-edge-{CRIBL_VERSION}", "cribl-edge")
        shutil.move("cribl-edge", CRIBL_DIR)
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to download or extract Cribl Edge: {e}")
    except FileNotFoundError as e:
        print(f"[!] Directory 'cribl-edge-{CRIBL_VERSION}' not found: {e}")

# ==== User and Permission Setup ====
def check_connectivity(host, port):
    print("[+] Checking connectivity to Cribl Stream Leader...")
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"Cribl Stream Leader is reachable at {host}:{port}")
            return True
    except socket.error:
        print(f"Cannot reach Cribl Stream Leader at {host}:{port}")
        return False

def create_user(username, groupname):
    try:
        pwd.getpwnam(username)
        print(f"[+] User {repr(username)} already exists")
    except KeyError:
        print(f"[+] Creating user {repr(username)}")
        subprocess.run(["useradd", "-r", "-s", "/bin/false", username], check=True)
    
    try:
        grp.getgrnam(groupname)
    except KeyError:
        subprocess.run(["groupadd", groupname], check=True)

def set_permissions(path, user, group):
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    for root, dirs, files in os.walk(path):
        os.chown(root, uid, gid)
        for d in dirs:
            os.chown(os.path.join(root, d), uid, gid)
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)

# ==== Cribl Commands ====
def run_as_cribl(cmd):
    full_cmd = ["sudo", "-u", CRIBL_USER] + cmd
    subprocess.run(full_cmd, check=True)

def bootstrap_edge():
    print("[+] Registering Edge with Leader...")
    os.chdir(f"{CRIBL_DIR}/cribl-edge")
    run_as_cribl([
        "./bin/cribl", "edge:bootstrap",
        "--edge-name", EDGE_NAME,
        "--controller", LEADER_URL,
        "--token", TOKEN
    ])

def enable_systemd():
    print("[+] Enabling Cribl as systemd service...")
    subprocess.run([
        "./bin/cribl", "boot-start", "enable",
        "--user", CRIBL_USER,
        "--group", CRIBL_GROUP
    ], cwd=f"{CRIBL_DIR}/cribl-edge", check=True)

def start_cribl():
    subprocess.run(["systemctl", "daemon-reexec"], check=True)
    subprocess.run(["systemctl", "start", "cribl"], check=True)
    subprocess.run(["systemctl", "enable", "cribl"], check=True)
    print("[+] Waiting for Cribl to start...")
    time.sleep(3)
    subprocess.run(["systemctl", "status", "cribl", "--no-pager"])

# ==== Fleet Management ====
def create_fleet():
    print("[+] Creating Fleet...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}"
    }
    data = {
        "name": FLEET_NAME,
        "description": "Fleet created via script"
    }
    response = requests.post(f"{LEADER_URL}/api/v1/fleets", headers=headers, data=json.dumps(data), verify=False)
    if response.status_code == 201:
        print(f"Fleet '{repr(FLEET_NAME)}' created successfully.")
    elif response.status_code == 409:
        print(f"Fleet '{repr(FLEET_NAME)}' already exists.")
    else:
        print(f"Failed to create Fleet: {repr(response.text)}")

def join_fleet():
    print("[+] Joining Fleet...")
    os.chdir(f"{CRIBL_DIR}/cribl-edge")
    run_as_cribl([
        "./bin/cribl", "edge:join-fleet",
        "--fleet", FLEET_NAME,
        "--controller", LEADER_URL,
        "--token", TOKEN
    ])

# ==== Main Execution ====
def main():
    if not check_connectivity(LEADER_IP, LEADER_PORT):
        sys.exit(1)

    create_user(CRIBL_USER, CRIBL_GROUP)
    download_and_extract_tarball()
    set_permissions(CRIBL_DIR, CRIBL_USER, CRIBL_GROUP)
    create_fleet()
    bootstrap_edge()
    join_fleet()
    enable_systemd()
    start_cribl()

    print(f"\n Cribl Edge installed, connected to Leader at {LEADER_URL}, and joined Fleet '{repr(FLEET_NAME)}'")

if __name__ == "__main__":
    main()
