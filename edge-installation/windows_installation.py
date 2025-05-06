import platform
import subprocess
import threading

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"Standard error: {result.stderr}")
    
    if result.returncode == 0:
        print("Installation done successfully.")
        # Disable TLS after installation
        disable_tls_command = 'some_command_to_disable_tls'  # Replace with actual command to disable TLS
        subprocess.run(disable_tls_command, shell=True)
    else:
        raise RuntimeError(f"Installation failed with return code {result.returncode}")

def install_windows(config):
    print("Windows installation command:")
    
    # Construct the msiexec command using values from the config file
    command = (
        f'msiexec /i "{config["For_Windows_cribl_pkg_url"]}" /qn '
        f'MODE="mode-managed-edge" HOSTNAME="{config["LEADER_IP"]}" PORT="4200" '
        f'AUTH="{config["EDGE_TOKEN"]}" FLEET="{config["FLEET_NAME"]}" '
        f'TLS="{config["TLS"]}" USERNAME="LocalSystem" '
        f'APPLICATIONROOTDIRECTORY="C:\\Program Files\\Cribl\\" '
        f'/l*v "{config["LOG_PATH"]}"'
    )
    
    if platform.system() == "Windows":
        print(f"Running command: {command}")
        # Run the command asynchronously
        thread = threading.Thread(target=run_command, args=(command,))
        thread.start()
    else:
        print("This script must be run in a Windows environment.")
