import subprocess
import socket
import urllib.parse

def run(command, check=True):
    print(f"\nRunning: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}")

def check_connectivity(leader_ip, leader_port):
    print(f"Checking connectivity to {leader_ip}:{leader_port}")
    try:
        with socket.create_connection((leader_ip, leader_port), timeout=5):
            print("Cribl Leader is reachable.")
    except Exception as e:
        raise RuntimeError(f"Could not connect to Cribl Leader at {leader_ip}:{leader_port}: {e}")

def create_user_group(cribl_user, cribl_group):
    print("Creating cribl system user and group if they don't exist")
    run(f"id -u {cribl_user} || sudo useradd -m -s /bin/bash {cribl_user}", check=False)
    run(f"getent group {cribl_group} || sudo groupadd {cribl_group}", check=False)
    run(f"sudo usermod -aG {cribl_group} {cribl_user}", check=False)

def set_permissions(install_dir, cribl_user, cribl_group):
    print("Ensuring permissions on installation directory")
    run(f"sudo mkdir -p {install_dir}")
    run(f"sudo chown -R {cribl_user}:{cribl_group} {install_dir}")

def restart_and_verify_service():
    print("Restarting Cribl Edge service")
    run("sudo systemctl restart cribl")
    run("sudo systemctl status cribl", check=False)

def install_linux(config):
    check_connectivity(config["LEADER_IP"], int(config["LEADER_PORT"]))
    create_user_group(config["CRIBL_USER"], config["CRIBL_GROUP"])
    set_permissions(config["INSTALL_DIR"], config["CRIBL_USER"], config["CRIBL_GROUP"])

    print("Installing Cribl Edge using the install-edge.sh script")
    encoded_dir = urllib.parse.quote(config["INSTALL_DIR"])
    url = f"http://{config['LEADER_IP']}:{config['LEADER_PORT']}/init/install-edge.sh" \
          f"?group={config['FLEET_NAME']}&token={config['EDGE_TOKEN']}" \
          f"&user={config['CRIBL_USER']}&user_group={config['CRIBL_GROUP']}&install_dir={encoded_dir}"
    run(f"curl '{url}' | bash -")

    restart_and_verify_service()
    print("Cribl Edge for Linux installed and started.")
