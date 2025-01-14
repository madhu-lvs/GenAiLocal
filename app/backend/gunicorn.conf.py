import multiprocessing
import os

# Maximum number of requests a worker will process before restarting
# This helps prevent memory leaks by ensuring workers are periodically refreshed
max_requests = 1000

# Maximum jitter to add to the max_requests setting
# This spreads out worker restarts to avoid all workers restarting at the same time
max_requests_jitter = 50

# Log file location. "-" means log to stdout.
log_file = "-"

# Network binding
bind = "0.0.0.0"

# Request timeout in seconds (230 is Azure App Service's hard limit)
# See: https://learn.microsoft.com/en-us/troubleshoot/azure/app-service/web-apps-performance-faqs#why-does-my-request-time-out-after-230-seconds
timeout = 230

# Calculate the number of worker processes based on CPU cores
num_cpus = multiprocessing.cpu_count()

# Worker process count calculation:
# - For Azure Free tier (which reports 2 CPUs), use single worker to avoid resource constraints
# - For all other tiers, use the formula: (num_cpus * 2) + 1
# This formula is based on Gunicorn's recommendations for handling both CPU-bound and I/O-bound applications
if os.getenv("WEBSITE_SKU") == "LinuxFree":
    # Free tier requires single worker despite reporting multiple CPUs
    workers = 1
else:
    # Standard formula for worker count: (2 * CPU cores) + 1
    workers = (num_cpus * 2) + 1

# Worker class specification
# Uses custom Uvicorn worker that provides enhanced async support and logging configuration
worker_class = "custom_uvicorn_worker.CustomUvicornWorker"