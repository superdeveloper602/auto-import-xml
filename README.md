# Auto-Import-XML

This repository contains the GitHub Actions workflow for automatically importing XML files using FTP details. The workflow retrieves files, processes them, and manages data import tasks into a PostgreSQL database.

## Prerequisites

Before you can run the automation jobs, you must configure the necessary secrets in your GitHub repository to securely store environment variables. These are crucial for the FTP connection and subsequent processing steps.

### Setting Up Secrets

You need to set up the following secrets in your GitHub repository:

- `FTP_SERVER`: The FTP server URL or IP address.
- `FTP_USERNAME`: The username for FTP access.
- `FTP_PASSWORD`: The password for FTP access.
- `XML_FOLDER_PATH`: The path where the XML files are stored on the FTP server.
- `IS_TESTING`: when testing let is be `true`, otherwise `false`

To add these secrets:
1. Go to your GitHub repository.
2. Navigate to **Settings** > **Secrets** > **Actions**.
3. Click on **New repository secret** for each of the items listed above and add the corresponding values.

