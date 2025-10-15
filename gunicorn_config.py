# Gunicorn configuration file for Turantalim
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 300
keepalive = 5

# Restart workers after this many requests, with jitter
graceful_timeout = 30
preload_app = False

# Logging
accesslog = "/home/user/turantalim/logs/gunicorn_access.log"
errorlog = "/home/user/turantalim/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "turantalim_gunicorn"

# Server mechanics
daemon = False
pidfile = "/home/user/turantalim/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Nginx)
keyfile = None
certfile = None

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Gunicorn is starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Gunicorn is reloading...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Gunicorn is ready. Listening on: {bind}")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} interrupted")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker {worker.pid} aborted")
