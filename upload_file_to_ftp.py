import ftplib

def upload_file(ftp_server, ftp_username, ftp_password, file_path, upload_path):
    """
    Upload a file to an FTP server.

    Args:
    ftp_server (str): FTP server address.
    ftp_username (str): FTP username.
    ftp_password (str): FTP password.
    file_path (str): Local path to the file to be uploaded.
    upload_path (str): Path including the filename under which the file will be stored on the FTP server.
    target_directory (str): Directory on the FTP server where the file will be uploaded.
    """
    # Connect to the FTP server
    ftp = ftplib.FTP(ftp_server)
    ftp.login(ftp_username, ftp_password)
    ftp.cwd('home')
    print(ftp.pwd())

    # Open the file in binary read mode
    with open(file_path, 'rb') as file:
        # Upload the file
        res = ftp.storbinary('STOR ' + upload_path, file)
        print(res)

    # Close the FTP connection
    ftp.quit()

# Example usage:
ftp_server = '127.0.0.1'
ftp_username = 'sherlock'
ftp_password = '123456'
local_file_path = 'data.xml'
upload_file_name = 'data.xml'

upload_file(ftp_server, ftp_username, ftp_password, local_file_path, upload_file_name)