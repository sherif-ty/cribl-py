import requests
import ssl

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings()

def connect_to_leader(protocol, host, port, token):
    # Construct the URL using the provided protocol, host, and port
    url = f"{protocol}://{host}:{port}/api/v1/version"
    
    # Set headers for the request with the authorization token
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print(f"[+] Trying {protocol.upper()} connection to {url}...")
        response = requests.get(url, headers=headers, timeout=5, verify=False)  # Disable SSL verification
        if response.status_code == 200:
            print(f"[+] Successfully connected to Cribl Leader at {url}")
        else:
            print(f"[!] Failed to connect, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection failed: {e}")

# Read the configuration from 'config.txt' (you can also hardcode values here)
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

# Read values from the config file
LEADER_IP = config['LEADER_IP']
LEADER_PORT = int(config['LEADER_PORT'])
LEADER_PROTOCOL = config['LEADER_PROTOCOL']
TOKEN = config['TOKEN']

# Call the function to connect to Cribl Leader
connect_to_leader(LEADER_PROTOCOL, LEADER_IP, LEADER_PORT, TOKEN)
