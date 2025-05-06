import sys
from windows_installation import install_windows

def load_config(file_path):
    config = {}
    with open(file_path) as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

def main():
    config = load_config("config.txt")
    try:
        if config["ENVIRONMENT"] == "windows":
            install_windows(config)
        else:
            raise ValueError(f"Unsupported environment: {config['ENVIRONMENT']}")
    except Exception as error:
        print(f"\nInstallation failed: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
