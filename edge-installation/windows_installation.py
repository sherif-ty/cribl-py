import platform
import subprocess

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
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Standard error: {result.stderr}")
        
        if result.returncode == 0:
            # Restart the Cribl service
            subprocess.run("net stop cribl", shell=True)
            subprocess.run("net start cribl", shell=True)
            print("Installation done successfully.")
        else:
            raise RuntimeError(f"Installation failed with return code {result.returncode}")
    else:
        print("This script must be run in a Windows environment.")



