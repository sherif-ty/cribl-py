import requests
import sys
import os
import platform
import subprocess

# ===========================
# Cribl Edge Configuration
# ===========================

CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"

LEADER_IP = "3.123.253.64"
LEADER_PORT = 4200
LEADER_PROTOCOL = "http"
CRIBL_DIR = "/opt/cribl"

# Fleet or sub-fleet to join or create.
# Examples:
#   "myfleet"           → top-level fleet
#   "myfleet/region1"   → sub-fleet
#   ""                  → join default fleet
FLEET_NAME = "python-fleet"

# Cribl Leader login credentials (used to create/check fleets)
USERNAME = "admin"
PASSWORD = "admin"

# ===========================
# Internal Variables
# ===========================

LEADER_URL = f"{LEADER_PROTOCOL}://{LEADER_IP}:{LEADER_PORT}"
SESSION = requests.Session()
AUTH_TOKEN = None

# ===========================
# Utility Functions
# ===========================

def run_command(command, check=True, shell=True, input_text=None):
    print(f"\n[Running] {command}")
    result = subprocess.run(
        command,
        shell=shell,
        input=input_text,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"[stderr] {result.stderr}")
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {command}")
        sys.exit(result.returncode)
    return result

def check_connectivity(ip, port):
    try:
        response = requests.get(f"http://{ip}:{port}", timeout=5)
        if response.status_code == 200:
            print("Connected to Cribl Leader successfully.")
            return True
        else:
            print(f"Cribl Leader responded with status code {response.status_code}")
            return False
    except requests.ConnectionError:
        print(f"Could not connect to Cribl Leader at {ip}:{port}")
        return False

def create_user_and_group(user, group):
    run_command(f"id -u {user} || sudo useradd -m -s /bin/bash {user}", check=False)
    run_command(f"getent group {group} || sudo groupadd {group}", check=False)
    run_command(f"sudo usermod -aG {group} {user}")

def download_and_extract_tarball():
    arch = platform.machine()
    if arch == "x86_64":
        run_command("curl -Lso - $(curl https://cdn.cribl.io/dl/latest-x64) | sudo tar zxv -C /opt")
    elif arch == "aarch64":
        run_command("curl -Lso - $(curl https://cdn.cribl.io/dl/latest-arm64) | sudo tar zxv -C /opt")
    else:
        print(f"Unsupported architecture: {arch}")
        sys.exit(1)

def set_permissions():
    run_command(f"sudo chown -R {CRIBL_USER}:{CRIBL_GROUP} {CRIBL_DIR}")

# ===========================
# Authentication
# ===========================

def login_and_get_token():
    global AUTH_TOKEN
    login_url = f"{LEADER_URL}/api/v1/auth/login"
    try:
        response = SESSION.post(login_url, json={"username": USERNAME, "password": PASSWORD})
        response.raise_for_status()
        AUTH_TOKEN = response.json().get("token")
        SESSION.headers.update({
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        })
        print("Successfully authenticated with Cribl Leader.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

# ===========================
# Fleet Management
# ===========================

def fleet_exists(fleet_name):
    if not fleet_name:
        return True
    url = f"{LEADER_URL}/api/v1/fleets"
    try:
        response = SESSION.get(url)
        response.raise_for_status()
        fleets = response.json().get("fleets", [])
        return any(fleet.get("name") == fleet_name for fleet in fleets)
    except Exception as e:
        print(f"Error checking for fleet: {e}")
        sys.exit(1)

def create_fleet(fleet_name):
    url = f"{LEADER_URL}/api/v1/fleets"
    payload = {"name": fleet_name}
    try:
        response = SESSION.post(url, json=payload)
        response.raise_for_status()
        print(f"Created fleet: {fleet_name}")
    except Exception as e:
        print(f"Failed to create fleet '{fleet_name}': {e}")
        sys.exit(1)

def ensure_fleet(fleet_name):
    if not fleet_name:
        print("No fleet name provided. Will use the default fleet.")
        return
    print(f"Checking if fleet '{fleet_name}' exists...")
    if fleet_exists(fleet_name):
        print(f"Fleet '{fleet_name}' already exists.")
    else:
        print(f"Fleet '{fleet_name}' does not exist. Creating it...")
        create_fleet(fleet_name)

# ===========================
# Cribl Edge Setup
# ===========================

def bootstrap_edge():
    if FLEET_NAME:
        run_command(f"sudo -u {CRIBL_USER} {CRIBL_DIR}/bin/cribl mode-edge -H {LEADER_IP} -p {LEADER_PORT} --group {FLEET_NAME}")
    else:
        run_command(f"sudo -u {CRIBL_USER} {CRIBL_DIR}/bin/cribl mode-edge -H {LEADER_IP} -p {LEADER_PORT}")

def enable_systemd():
    run_command(f"sudo {CRIBL_DIR}/bin/cribl boot-start enable -m systemd -u {CRIBL_USER}", input_text="y\n")

def start_cribl():
    run_command("sudo systemctl start cribl")
    run_command("sudo systemctl status cribl", check=False)

def verify_install():
    print("\nVerifying Cribl installation...")
    run_command(f"ls -l {CRIBL_DIR}", check=False)
    run_command(f"sudo tail -n 20 {CRIBL_DIR}/log/cribl.log", check=False)

# ===========================
# Main Execution
# ===========================

def main():
    if not check_connectivity(LEADER_IP, LEADER_PORT):
        sys.exit(1)

    login_and_get_token()
    create_user_and_group(CRIBL_USER, CRIBL_GROUP)
    download_and_extract_tarball()
    set_permissions()

    ensure_fleet(FLEET_NAME)
    bootstrap_edge()
    enable_systemd()
    start_cribl()
    verify_install()

    print("\nInstallation complete.")
    print(f"Cribl Edge is connected to Leader at {LEADER_URL}")
    if FLEET_NAME:
        print(f"Joined Fleet: {FLEET_NAME}")
    else:
        print("Joined default fleet.")

if __name__ == "__main__":
    main()
