import os
import json
import zipfile
import hashlib
import requests

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def main():
    print("Fetching version manifest...")
    response = requests.get(MANIFEST_URL)
    manifest = response.json()

    # Filter for all official releases
    releases = [v for v in manifest['versions'] if v['type'] == 'release']

    # Keep track of the last hash to skip duplicate identical asset sets
    last_hash = None

    for version in releases:
        v_id = version['id']
        v_url = version['url']

        zip_name = f"mc-assets-data-{v_id}.zip"

        # If the zip already exists locally (or cached), check it
        if os.path.exists(zip_name):
            print(f"Skipping {v_id}: Archive already exists.")
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

        # Extract assets, data, and legacy paths based on version structure
        with zipfile.ZipFile(jar_path, 'r') as jar:
            for file in jar.namelist():
                # Modern versions (1.7+) use assets/ and data/
                if file.startswith("assets/") or file.startswith("data/"):
                    jar.extract(file, extracted_dir)
                # Legacy versions (1.0 - 1.6) store textures and structures in root/other folders
                elif any(file.startswith(p) for p in ["mob/", "item/", "terrain/", "font/", "gui/", "sound/", "music/", "title/"]):
                    jar.extract(file, extracted_dir)

        # Zip valid target folders together
        print(f"Zipping contents into {zip_name}...")
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            valid_folders = ["assets", "data", "mob", "item", "terrain", "font", "gui", "sound", "music", "title"]
            for prefix in valid_folders:
                target_path = os.path.join(extracted_dir, prefix)
                if os.path.exists(target_path):
                    for root, dirs, files in os.walk(target_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, extracted_dir)
                            zipf.write(file_path, arcname)

        # Cleanup temporary jar and raw files
        if os.path.exists(jar_path):
            os.remove(jar_path)

        # Deduplication check: Compare hash with the previous version
        if os.path.exists(zip_name):
            current_hash = get_file_hash(zip_name)
            if current_hash == last_hash:
                print(f"Version {v_id} assets are identical to previous version. Removing duplicate zip.")
                os.remove(zip_name)
            else:
                last_hash = current_hash

        print(f"Finished processing version {v_id}!")

if __name__ == "__main__":
    main()
