from uvicorn.workers import UvicornWorker

# Logging configuration dictionary that defines the format and handling of log messages
# This configuration ensures consistent logging across both standard error and standard output streams
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # Default formatter for general logging
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
        # Access formatter for HTTP request logging
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "format": "%(asctime)s - %(message)s",
        },
    },
    "handlers": {
        # Handler for general application logs
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        # Handler for HTTP access logs
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # Root logger configuration
        "root": {
            "handlers": ["default"],
        },
        # Uvicorn error logger configuration
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["default"],
            "propagate": False,
        },
        # Uvicorn access logger configuration
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["access"],
            "propagate": False,
        },
    },
}


class CustomUvicornWorker(UvicornWorker):
    """
    Custom Uvicorn worker class for Gunicorn that provides specialized logging configuration.
    
    This worker class extends the standard UvicornWorker to include a custom logging
    configuration that separates error and access logs into different streams with
    different formatting.

    The worker uses stderr for application logs and stdout for access logs, making
    it easier to filter and analyze different types of logs in production environments.

    Configuration:
        - Application logs (stderr):
          Format: "[timestamp] - [log level] - [message]"
          Example: "2024-03-07 10:15:30 - INFO - Application started"

        - Access logs (stdout):
          Format: "[timestamp] - [HTTP request details]"
          Example: "2024-03-07 10:15:35 - GET /api/status 200"

    Attributes:
        CONFIG_KWARGS (dict): Configuration settings applied to all worker instances,
            containing the logging configuration dictionary.

    Usage:
        This worker is typically specified in a Gunicorn configuration file or
        command line using the '-k' or '--worker-class' option:
        
        gunicorn -k custom_uvicorn_worker.CustomUvicornWorker myapp:app
    """

    CONFIG_KWARGS = {
        "log_config": logconfig_dict,
    }