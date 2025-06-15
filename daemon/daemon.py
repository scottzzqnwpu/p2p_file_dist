import os
import time
import json
import subprocess
import logging
import sys
from hdfs import InsecureClient
from pathlib import Path

HDFS_WEB_FS_URL = "http://192.168.3.14:9870/webhdfs/v1"
CONFIG_PATH = "./config.json"
HDFS_CLIENT = InsecureClient("http://192.168.3.14:9870", user="hdfs")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def list_hdfs_dirs(path, get_files=False):
    try:
        if get_files:
            return sorted([f for f in HDFS_CLIENT.list(path, status=False)], reverse=True)
        else:
            return sorted([d for d in HDFS_CLIENT.list(path, status=False) if HDFS_CLIENT.status(f"{path}/{d}").get('type') == 'DIRECTORY'], reverse=True)
    except Exception as e:
        logger.info(f"[ERROR] list_hdfs_dirs({path}, get_files={get_files}): {e}")
        return []

def download_with_dragonfly(hdfs_path, local_path):
    logger.info(f"[INFO] Downloading {hdfs_path} to {local_path}")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    logger.info(f"[INFO] origin hdfs_path: {hdfs_path}")
    webfs_url = HDFS_WEB_FS_URL + hdfs_path + "?op=OPEN"
    logger.info(f"[INFO] WebFS URL: {webfs_url}")
    subprocess.run(["dfget", "--url", webfs_url, "--output", local_path], check=False)

def clean_old_versions(local_dir, keep=2):
    try:
        versions = sorted([d for d in os.listdir(local_dir) if os.path.isdir(os.path.join(local_dir, d))], reverse=True)
        for old in versions[keep:]:
            path_to_delete = os.path.join(local_dir, old)
            logger.info(f"[INFO] Removing old version: {path_to_delete}")
            subprocess.run(["rm", "-rf", path_to_delete], check=True)
    except Exception as e:
        logger.info(f"[ERROR] clean_old_versions({local_dir}): {e}")

def sync():
    config = load_config()
    for item in config["monitor_paths"]:
        hdfs_base = item["hdfs_path"]
        local_base = item["local_path"]

        os.makedirs(local_base, exist_ok=True)

        hdfs_versions = list_hdfs_dirs(hdfs_base)
        local_versions = os.listdir(local_base) if os.path.exists(local_base) else []

        for version in hdfs_versions:
            if version not in local_versions:
                hdfs_version_path = f"{hdfs_base}/{version}"
                local_version_path = os.path.join(local_base, version)

                files_in_version = list_hdfs_dirs(hdfs_version_path, get_files=True)
                for file in files_in_version:
                    file_hdfs_path = f"{hdfs_version_path}/{file}"
                    file_local_path = os.path.join(local_version_path, file)
                    download_with_dragonfly(file_hdfs_path, file_local_path)

        clean_old_versions(local_base)

def daemon_loop():
    logger.info("[INFO] Starting daemon...")
    while True:
        try:
            sync()
        except Exception as e:
            logger.error(f"[ERROR] {e}")
        time.sleep(load_config().get("check_interval_seconds", 300))

if __name__ == "__main__":
    daemon_loop()
