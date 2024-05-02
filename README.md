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

### Remove the artifact after 3 days run the import xml

To ensure that artifacts are automatically removed after 3 days, follow these steps to configure the GitHub settings:

1. Go to your repository's settings.
2. Click on "Actions" in the left sidebar.
3. Under "Artifact and log retention" section, set the "Artifact retention period" to "3 days".
4. Click "Save" to apply the changes.

With this setting, GitHub will automatically remove artifacts older than 3 days from your repository. After 3 days, you can run the `import xml` command to process the artifacts before they are removed.