import requests
import sys
import os
import platform
import subprocess

# Configuration
CRIBL_USER = "cribl"
CRIBL_GROUP = "cribl"
EDGE_NAME = "python-edge"
LEADER_IP = "3.123.253.64"
LEADER_PORT = 4200
CRIBL_DIR = "/opt/cribl"
TOKEN = "eOHdmkvEJsN3QQvDz8T7tkQpV9SnYEqZ"
FLEET_NAME = "python-fleet"
LEADER_PROTOCOL = "http"

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
            print("[✓] Cribl Leader is reachable")
            return True
        else:
            print(f"[x] Cribl Leader responded with status code {response.status_code}")
            return False
    except requests.ConnectionError:
        print(f"[x] Could not connect to {ip}:{port}")
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
        print(f"[x] Unsupported architecture: {arch}")
        sys.exit(1)

def set_permissions():
    run_command(f"sudo chown -R {CRIBL_USER}:{CRIBL_GROUP} {CRIBL_DIR}")

def bootstrap_edge():
    run_command(f"sudo -u {CRIBL_USER} {CRIBL_DIR}/bin/cribl mode-edge -H {LEADER_IP} -p {LEADER_PORT}")

def enable_systemd():
    run_command(f"sudo {CRIBL_DIR}/bin/cribl boot-start enable -m systemd -u {CRIBL_USER}", input_text="y\n")

def start_cribl():
    run_command("sudo systemctl start cribl")
    run_command("sudo systemctl status cribl", check=False)

def verify_install():
    print("\n[✓] Checking Cribl installation directory:")
    run_command(f"ls -l {CRIBL_DIR}", check=False)
    print("\n[✓] Tail of Cribl log:")
    run_command(f"sudo tail -n 20 {CRIBL_DIR}/log/cribl.log", check=False)

def main():
    if not check_connectivity(LEADER_IP, LEADER_PORT):
        sys.exit(1)

    create_user_and_group(CRIBL_USER, CRIBL_GROUP)
    download_and_extract_tarball()
    set_permissions()
    bootstrap_edge()
    enable_systemd()
    start_cribl()
    verify_install()

    print(f"\n Cribl Edge installed and connected to Leader at {LEADER_PROTOCOL}://{LEADER_IP}:{LEADER_PORT}")

if __name__ == "__main__":
    main()
