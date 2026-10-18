import os
import json
import requests

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def main():
    print("Fetching Minecraft version manifest...")
    response = requests.get(MANIFEST_URL)
    manifest = response.json()

    # Let's inspect the latest release version as a starting point
    latest_release = manifest['latest']['release']
    print(f"Latest release found: {latest_release}")

    for version in manifest['versions']:
        if version['id'] == latest_release:
            print(f"Found metadata for {version['id']}, fetching download URL...")
            v_data = requests.get(version['url']).json()
            client_url = v_data['downloads']['client']['url']
            print(f"Client JAR URL: {client_url}")
            # Asset extraction logic goes here
            break

if __name__ == "__main__":
    main()
