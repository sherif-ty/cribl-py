import requests
import sys
import os

# ----------------------------
# Basic Configuration
# ----------------------------

# User and group that will run Cribl Edge on the system
CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"

# Cribl Leader connection details
LEADER_IP = "3.123.253.64"
LEADER_PORT = 4200
LEADER_PROTOCOL = "http"

# Cribl Edge will be installed into this directory
INSTALL_DIR = "/opt/cribl"

# Login credentials to the Cribl Leader (used to create/check fleets)
USERNAME = "admin"
PASSWORD = "admin"

# Token used only for Edge node registration
EDGE_INSTALL_TOKEN = "eOHdmkvEJsN3QQvDz8T7tkQpV9SnYEqZ"

# The name of the fleet or sub-fleet you want to use.
# Examples:
# - "myfleet" will join or create a top-level fleet
# - "myfleet/region1" will join or create a sub-fleet
# - "" (empty string) will skip creation and join the default fleet
FLEET_NAME = "python-fleet"

# ----------------------------
# Internal Setup
# ----------------------------

LEADER_URL = f"{LEADER_PROTOCOL}://{LEADER_IP}:{LEADER_PORT}"
SESSION = requests.Session()

# Headers used for all requests after login
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ----------------------------
# Step 1: Login and Get Token
# ----------------------------

def login_to_leader():
    print("Logging in to Cribl Leader...")
    try:
        response = SESSION.post(
            f"{LEADER_URL}/api/v1/auth/login",
            json={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            raise Exception("No token found in login response.")
        HEADERS["Authorization"] = f"Bearer {token}"
        print("Logged in successfully.")
    except Exception as e:
        print(f"Login failed: {e}")
        sys.exit(1)

# ----------------------------
# Step 2: Fleet Handling
# ----------------------------

def check_if_fleet_exists():
    if not FLEET_NAME:
        return True  # Skip check if joining default fleet
    try:
        response = SESSION.get(f"{LEADER_URL}/api/v1/fleets", headers=HEADERS)
        response.raise_for_status()
        fleets = response.json().get("fleets", [])
        return any(f.get("name") == FLEET_NAME for f in fleets)
    except Exception as e:
        print(f"Error checking for fleet: {e}")
        sys.exit(1)

def create_fleet():
    if not FLEET_NAME:
        return
    try:
        response = SESSION.post(
            f"{LEADER_URL}/api/v1/fleets",
            json={"name": FLEET_NAME},
            headers=HEADERS
        )
        response.raise_for_status()
        print(f"Fleet '{FLEET_NAME}' created.")
    except Exception as e:
        print(f"Failed to create fleet: {e}")
        sys.exit(1)

def ensure_fleet_exists():
    if not FLEET_NAME:
        print("No fleet name provided. Will use the default fleet.")
        return
    print(f"Checking if fleet '{FLEET_NAME}' exists...")
    if check_if_fleet_exists():
        print(f"Fleet '{FLEET_NAME}' already exists.")
    else:
        print(f"Fleet '{FLEET_NAME}' does not exist. Creating it now...")
        create_fleet()

# ----------------------------
# Step 3: Install Cribl Edge
# ----------------------------

def run_edge_install():
    print("Starting Cribl Edge installation...")
    url = (
        f"{LEADER_URL}/init/install-edge.sh?"
        f"group={FLEET_NAME}&"
        f"token={EDGE_INSTALL_TOKEN}&"
        f"user={CRIBL_USER}&"
        f"user_group={CRIBL_GROUP}&"
        f"install_dir={INSTALL_DIR}"
    )
    install_command = f"curl '{url}' | bash -"
    print(f"Executing: {install_command}")
    os.system(install_command)

# ----------------------------
# Main Program
# ----------------------------

def main():
    login_to_leader()
    ensure_fleet_exists()
    run_edge_install()
    print("Cribl Edge installation complete.")
    if FLEET_NAME:
        print(f"Edge joined fleet: {FLEET_NAME}")
    else:
        print("Edge joined the default fleet.")

if __name__ == "__main__":
    main()
