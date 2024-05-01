import ftplib
import pandas as pd
import xport
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()
# FTP Details
ftp_server = os.getenv('FTP_SERVER')
ftp_username = os.getenv('FTP_USERNAME')
ftp_password = os.getenv('FTP_PASSWORD')
path = os.getenv('XML_FILE_PATH')

directory_path = os.path.dirname(path)
file_name = os.path.basename(path)
print(directory_path, file_name)

# Connect to FTP and download file
ftp = ftplib.FTP(ftp_server)
ftp.login(ftp_username, ftp_password)
print(ftp.dir())
ftp.cwd(directory_path)
with open(file_name, 'wb') as file:
    ftp.retrbinary("RETR " + file_name, file.write)
ftp.quit()

# Read the downloaded SAS transport file
with open(file_name, 'rb') as file:
    contents = file.read()

soup = BeautifulSoup(contents, 'xml')

with open('data.xml', 'w', encoding='utf-8') as file:
    file.write(soup.prettify())