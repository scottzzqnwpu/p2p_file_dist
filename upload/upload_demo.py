import requests
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def webhdfs_upload(local_file, hdfs_path, webhdfs_host="http://192.168.3.14:9870", user="hdfs"):
    # Step 1: Create parent directories
    dir_path = "/".join(hdfs_path.strip("/").split("/")[:-1])
    mkdir_url = f"{webhdfs_host}/webhdfs/v1/{dir_path}?op=MKDIRS&user.name={user}"
    logger.info(f"creative dir: {dir_path}, url: {mkdir_url}")
    requests.put(mkdir_url)

    # Step 2: Ask for upload redirect URL
    create_url = f"{webhdfs_host}/webhdfs/v1/{hdfs_path.lstrip('/')}?op=CREATE&user.name={user}"
    r = requests.put(create_url, allow_redirects=False)
    redirect_url = r.headers['Location'].replace("http://c4a015bc3af4:9864", "http://192.168.3.14:9864")
    logger.info(f"create_url: {dir_path}, redirect_url: {redirect_url}")
    
    
    # Step 3: Upload file`1`
    with open(local_file, 'rb') as f:
        r = requests.put(redirect_url, data=f)
        logger.info(f"upload_res: {r.status_code}")
        return r.status_code == 201

if __name__ == "__main__":
    # Example usage
    # Ensure the local file 'hello.txt' exists before running this
    # and that the HDFS path is correct.
    #webhdfs_upload("hello_v1.txt", "/dicts/dict_a/202506151100/hello_v1.txt")
    #webhdfs_upload("hello_v2.txt", "/dicts/dict_a/202506151200/hello_v2.txt")
    webhdfs_upload("hello_v3.txt", "/dicts/dict_a/202506151300/hello_v3.txt")