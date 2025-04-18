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

# ==== Configuration ====
CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"
EDGE_NAME = "edge-server2"
LEADER_IP = "10.0.0.1"  # Replace with Cribl Stream IP
LEADER_PORT = 4200
LEADER_URL = f"https://{LEADER_IP}:{LEADER_PORT}"
CRIBL_VERSION = "4.5.2"
CRIBL_TARBALL = f"cribl-edge-{CRIBL_VERSION}-linux-x64.tgz"
CRIBL_DIR = "/opt/cribl"
TOKEN = "your-token-from-stream-ui"  # Replace with actual token

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
        print(f"[+] User {username} already exists")
    except KeyError:
        print(f"[+] Creating user {username}")
        subprocess.run(["useradd", "-r", "-s", "/bin/false", username], check=True)
    
    try:
        grp.getgrnam(groupname)
    except KeyError:
        subprocess.run(["groupadd", groupname], check=True)

def download_and_extract_tarball():
    os.makedirs(CRIBL_DIR, exist_ok=True)
    os.chdir("/opt")
    
    url = f"https://cdn.cribl.io/dl/{CRIBL_TARBALL}"
    print(f"[+] Downloading {url}")
    urllib.request.urlretrieve(url, CRIBL_TARBALL)

    print(f"[+] Extracting {CRIBL_TARBALL}")
    with tarfile.open(CRIBL_TARBALL, "r:gz") as tar:
        tar.extractall()
    os.remove(CRIBL_TARBALL)
    os.rename(f"cribl-edge-{CRIBL_VERSION}", "cribl-edge")
    shutil.move("cribl-edge", CRIBL_DIR)

def set_permissions(path, user, group):
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    for root, dirs, files in os.walk(path):
        os.chown(root, uid, gid)
        for d in dirs:
            os.chown(os.path.join(root, d), uid, gid)
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)

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

def main():
    if not check_connectivity(LEADER_IP, LEADER_PORT):
        sys.exit(1)
    
    create_user(CRIBL_USER, CRIBL_GROUP)
    download_and_extract_tarball()
    set_permissions(CRIBL_DIR, CRIBL_USER, CRIBL_GROUP)
    bootstrap_edge()
    enable_systemd()
    start_cribl()

    print(f"\n Cribl Edge installed and connected to Leader at {LEADER_URL}")

if __name__ == "__main__":
    main()

