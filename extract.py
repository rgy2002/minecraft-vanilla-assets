import os
import json
import zipfile
import requests

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def main():
    print("Fetching version manifest...")
    response = requests.get(MANIFEST_URL)
    manifest = response.json()

    releases = [v for v in manifest['versions'] if v['type'] == 'release']

    for version in releases:
        v_id = version['id']
        v_url = version['url']

        zip_name = f"mc-assets-data-{v_id}.zip"
        # Skip if we already processed this version in a previous run
        if os.path.exists(zip_name):
            print(f"Skipping {v_id} (already zipped).")
            continue

        print(f"\nProcessing Minecraft version: {v_id}")
        v_data = requests.get(v_url).json()
        if 'client' not in v_data['downloads']:
            print(f"Skipping {v_id}: No client download available.")
            continue

        client_url = v_data['downloads']['client']['url']

        # Download client jar
        jar_path = f"client_{v_id}.jar"
        try:
            jar_data = requests.get(client_url).content
            with open(jar_path, "wb") as f:
                f.write(jar_data)
        except Exception as e:
            print(f"Failed to download {v_id}: {e}")
            continue

        extracted_dir = f"extracted_{v_id}"
        os.makedirs(extracted_dir, exist_ok=True)

        # Extract assets and data (note: very old versions like 1.0-1.6 structure paths differently)
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for file in jar.namelist():
                if file.startswith("assets/") or file.startswith("data/"):
                    jar.extract(file, extracted_dir)

        # Zip folders together
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

        # Cleanup jar and raw files to save disk space
        if os.path.exists(jar_path):
            os.remove(jar_path)
        print(f"Finished packaging version {v_id}!")

if __name__ == "__main__":
    main()
