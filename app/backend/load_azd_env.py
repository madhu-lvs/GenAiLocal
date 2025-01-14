import json
import logging
import subprocess
from typing import NoReturn, Optional

from dotenv import load_dotenv

# Configure module logger
logger = logging.getLogger("scripts")


def load_azd_env() -> None:
    """
    Load Azure Developer CLI (azd) environment variables into the current process.
    
    This function performs the following steps:
    1. Executes 'azd env list' to get all available environments
    2. Identifies the default environment from the list
    3. Loads the environment variables from the default environment's .env file
    
    The function uses the python-dotenv package to load the environment variables,
    which allows for overriding existing environment variables.
    
    Example:
        # Load azd environment variables at application startup
        if not running_on_azure:
            load_azd_env()
            # Environment variables are now available via os.environ
    
    Raises:
        Exception: If azd command fails or no default environment is found
            - This can happen if azd is not installed
            - This can happen if no azd environment has been initialized
            - This can happen if the default environment is not set
    
    Notes:
        - Requires azd CLI to be installed and available in PATH
        - Requires at least one azd environment to be initialized
        - Will override existing environment variables if they exist
        - Uses the 'scripts' logger for logging operations
    """
    # Execute azd command to list environments in JSON format
    result = subprocess.run(
        "azd env list -o json",
        shell=True,
        capture_output=True,
        text=True
    )

    # Check if the command executed successfully
    if result.returncode != 0:
        logger.error("Failed to execute 'azd env list' command")
        raise Exception("Error loading azd env")

    # Parse the JSON output
    env_json = json.loads(result.stdout)
    env_file_path = None

    # Find the default environment
    for entry in env_json:
        if entry["IsDefault"]:
            env_file_path = entry["DotEnvPath"]
            break

    # Validate that a default environment was found
    if not env_file_path:
        logger.error("No default azd environment found")
        raise Exception("No default azd env file found")

    # Load the environment variables
    logger.info(f"Loading azd env from {env_file_path}")
    load_dotenv(env_file_path, override=True)