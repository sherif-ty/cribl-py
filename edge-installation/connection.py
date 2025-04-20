import requests

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings()

def detect_leader_protocol(protocol, host, port):
    # List of protocols to try
    protocols = [protocol, 'https' if protocol == 'http' else 'http']
    
    for prot in protocols:
        try:
            url = f"{prot}://{host}:{port}/api/v1/version"
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code == 200:
                print(f"[+] Detected working protocol: {prot.upper()}")
                return f"{prot}://{host}:{port}"
        except requests.exceptions.RequestException as e:
            print(f"[!] {prot.upper()} failed: {e}")

    # If both protocols fail
    raise Exception(f"Could not connect to Cribl Leader using either HTTP or HTTPS")

# Input configuration
LEADER_IP = "3.123.253.64"  # Replace with your Cribl Leader IP
LEADER_PORT = 9000  # Replace with your Cribl Leader port (e.g., 9000)
LEADER_PROTOCOL = "http"  # or "https", based on what you expect

# Test connection
try:
    LEADER_URL = detect_leader_protocol(LEADER_PROTOCOL, LEADER_IP, LEADER_PORT)
    print(f"[+] Successfully connected to the Cribl Leader at {LEADER_URL}")
except Exception as e:
    print(f"[!] Error: {e}")
