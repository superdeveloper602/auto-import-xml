import ftplib
import pandas as pd
import xport
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import paramiko
import tarfile
import zipfile
import datetime

def get_current_date():
    today = datetime.datetime.now()
    return today.strftime("%Y-%m-%d")

def extract_file(local_file_path, extract_to):
    if local_file_path.endswith('.tar.gz'):
        with tarfile.open(local_file_path, 'r:gz') as tar:
            tar.extractall(path=extract_to)
            print(f"Extracted {local_file_path} into {extract_to}")
    elif local_file_path.endswith('.zip'):
        with zipfile.ZipFile(local_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            print(f"Extracted {local_file_path} into {extract_to}")

def progress_callback(transferred, total):
    print(f"Transferred: {transferred}, Total: {total}, Progress: {100 * (transferred / total):.2f}%")

def download_and_extract_files():
    load_dotenv()
    # FTP Details
    ftp_server = os.getenv('FTP_SERVER')
    ftp_username = os.getenv('FTP_USERNAME')
    ftp_password = os.getenv('FTP_PASSWORD')
    remote_dir = os.getenv('XML_FILE_PATH')
    is_testing = os.getenv('IS_TESTING')

    local_dir = './'

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    with paramiko.Transport((ftp_server, 22)) as transport:
        # Adjust the SFTP session parameters
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE
        transport.packetizer.REKEY_BYTES = pow(2, 40)  # 1TB max
        transport.packetizer.REKEY_PACKETS = pow(2, 40)

        transport.connect(username=ftp_username, password=ftp_password)
        with paramiko.SFTPClient.from_transport(transport) as sftp:
            sftp.chdir(remote_dir)
            file_list = sftp.listdir()
            current_date = get_current_date()
            print("current_date: ", current_date)
            files_to_download = []
            if is_testing == 'true':
                files_to_download = file_list
            else:
                files_to_download = [f for f in file_list if (f.endswith('.tar.gz') or f.endswith('.zip')) and current_date in f]
            print(f"Files to download: {files_to_download}")

            for file_name in files_to_download:
                remote_file_path = file_name
                local_file_path = os.path.join(local_dir, file_name)
                sftp.get(remote_file_path, local_file_path, callback=progress_callback)
                print(f"Downloaded {file_name} to {local_file_path}")

                data_dir = os.path.join(local_dir, 'data')
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                extract_file(local_file_path, data_dir)
                os.remove(local_file_path)
            print(f"File downloads and extraction completed successfully.")



download_and_extract_files()