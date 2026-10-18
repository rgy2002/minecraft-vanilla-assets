import os
import json
import zipfile
import requests

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def main():
    print("Fetching version manifest...")
    response = requests.get(MANIFEST_URL)
    manifest = response.json()

    # Target all releases (or slice it if you want a specific range)
    releases = [v for v in manifest['versions'] if v['type'] == 'release']

    # For testing/running safely within action limits, you can loop through them or target specific ones.
    # Let's process the latest release as an example, or loop through all:
    for version in releases[:5]:  # Change slice or remove it to process all from 1.0 onwards
        v_id = version['id']
        v_url = version['url']
        print(f"\nProcessing Minecraft version: {v_id}")

        v_data = requests.get(v_url).json()
        if 'client' not in v_data['downloads']:
            print(f"Skipping {v_id}: No client download available.")
            continue

        client_url = v_data['downloads']['client']['url']

        # Download client jar
        jar_path = f"client_{v_id}.jar"
        jar_data = requests.get(client_url).content
        with open(jar_path, "wb") as f:
            f.write(jar_data)

        extracted_dir = f"extracted_{v_id}"
        os.makedirs(extracted_dir, exist_ok=True)

        # Extract both assets and data folders from the jar
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for file in jar.namelist():
                if file.startswith("assets/") or file.startswith("data/"):
                    jar.extract(file, extracted_dir)

        # Zip both folders together into a single archive
        zip_name = f"mc-assets-data-{v_id}.zip"
        print(f"Zipping assets and data into {zip_name}...")
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for prefix in ["assets", "data"]:
                target_path = os.path.join(extracted_dir, prefix)
                if os.path.exists(target_path):
                    for root, dirs, files in os.walk(target_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, extracted_dir)
                            zipf.write(file_path, arcname)

        # Cleanup temporary files for this version
        os.remove(jar_path)
        print(f"Finished packaging version {v_id}!")
        break # Remove 'break' if you want it to process multiple versions in a single workflow run

if __name__ == "__main__":
    main()
