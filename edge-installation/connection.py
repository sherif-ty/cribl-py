import requests

LEADER_URL = "http://3.123.253.64:9000"
TOKEN = "criblmaster"
INSTALL_SCRIPT = "/init/install-edge.sh"
INSTALL_DIR = "/opt/cribl"
FLEET_GROUP = "default_fleet"
USER = "cribl"
USER_GROUP = "cribl"

# Construct URL for the installation script with query parameters
url = f"{LEADER_URL}{INSTALL_SCRIPT}?group={FLEET_GROUP}&token={TOKEN}&user={USER}&user_group={USER_GROUP}&install_dir={INSTALL_DIR}"

# Send GET request to fetch and execute the installation script
response = requests.get(url)
if response.status_code == 200:
    print("[+] Installation script fetched successfully. Running it...")
    # You can execute the script if needed, or just download it for manual use.
    with open("/tmp/install-edge.sh", "wb") as f:
        f.write(response.content)
    print("[+] Script saved to /tmp/install-edge.sh")
else:
    print(f"[!] Failed to fetch installation script. Status code: {response.status_code}")
