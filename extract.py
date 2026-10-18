import os
import json
import zipfile
import requests

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def main():
    response = requests.get(MANIFEST_URL)
    manifest = response.json()
    latest_release = manifest['latest']['release']
    print(f"Latest release: {latest_release}")

    for version in manifest['versions']:
        if version['id'] == latest_release:
            v_data = requests.get(version['url']).json()
            client_url = v_data['downloads']['client']['url']

            # Download client jar
            print(f"Downloading client JAR for {latest_release}...")
            jar_data = requests.get(client_url).content
            jar_path = "client.jar"
            with open(jar_path, "wb") as f:
                f.write(jar_data)

            # Extract assets folder from jar
            print("Extracting assets...")
            assets_dir = "extracted_assets"
            os.makedirs(assets_dir, exist_ok=True)

            with zipfile.ZipFile(jar_path, 'r') as jar:
                for file in jar.namelist():
                    if file.startswith("assets/"):
                        jar.extract(file, assets_dir)

            # Zip the extracted assets
            zip_name = f"mc-assets-{latest_release}.zip"
            print(f"Zipping into {zip_name}...")
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(os.path.join(assets_dir, "assets")):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, assets_dir)
                        zipf.write(file_path, arcname)

            print("Asset packaging complete!")
            break

if __name__ == "__main__":
    main()
