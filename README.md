# Project Setup Guide

This guide outlines the steps to set up and deploy the project in your Azure DEV environment.

## Prerequisites

Ensure the following are installed and configured before setting up the project:

- **Python**: Version 3.11 or above
- **Node.js**: Version 14 or above
- **PowerShell**: Version 7 or above
- **Azure CLI**: Installed and authenticated
- **Azure Developer CLI (azd)**: Installed and authenticated
- **Azure Account**: Must be a *Pay-As-You-Go* or above subscription (not the free tier)
- **Azure Subscription**: Ensure you have a subscription created in the [Azure Portal](https://portal.azure.com/)

## Setup Steps

1. **Authenticate to Azure:**
    ```bash
    az login
    ```

2. **Authenticate with Azure Developer CLI (azd):**
    ```bash
    azd auth login
    ```

3. **Create RG for your App with Azure CLI (azd):**
    ```bash
    az group create --name my-predefined-resource-group
    ```

5. **Document Ingestion process:**
    - In the root directory of the project, create a folder named `data`.
    - Add the ingestion files required by your project into the `data` folder.

4. **Deploy the project infrastructure:**
    ```bash
    azd up
    ```

6. **Deploy the Application:**
    ```bash
    azd deploy
    ```

Once the above steps are complete, your project will be set up and ready for use.
