#!/usr/bin/env python3

from docker import APIClient
import socketserver
import datetime
import errno
import json
import os
import signal
import socket
import threading
import time
from urllib.parse  import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer

PLUGIN_ID="volume-count"
PLUGIN_UNIX_SOCK="/var/run/scope/plugins/" + PLUGIN_ID + ".sock"
DOCKER_SOCK="unix://var/run/docker.sock"

nodes = {}

def update_loop():
    global nodes
    next_call = time.time()
    while True:
        # Get current timestamp in RFC3339
        timestamp = datetime.datetime.utcnow()
        timestamp = timestamp.isoformat('T') + 'Z'

        # Fetch and convert data to scope data model
        new = {}
        for container_id, volume_count in container_volume_counts().items():
            new["%s;<container>" % (container_id)] = {
                'latest': {
                    'volume_count': {
                        'timestamp': timestamp,
                        'value': str(volume_count),
                    }
                }
            }

        nodes = new
        next_call += 5
        time.sleep(next_call - time.time())

def start_update_loop():
    updateThread = threading.Thread(target=update_loop)
    updateThread.daemon = True
    updateThread.start()

# List all containers, with the count of their volumes
def container_volume_counts():
    containers = {}
    cli = APIClient(base_url=DOCKER_SOCK, version='auto')
    for c in cli.containers(all=True):
        containers[c['Id']] = len(c['Mounts'])
    return containers


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # The logger requires a client_address, but unix sockets don't have
        # one, so we fake it.
        self.client_address = "-"

        # Generate our json body
        body = json.dumps({
            'Plugins': [
                {
                    'id': PLUGIN_ID,
                    'label': 'Volume Counts',
                    'description': 'Shows how many volumes each container has mounted',
                    'interfaces': ['reporter'],
                    'api_version': '1',
                }
            ],
            'Container': {
                'nodes': nodes,
                # Templates tell the UI how to render this field.
                'metadata_templates': {
                    'volume_count': {
                        # Key where this data can be found.
                        'id': "volume_count",
                        # Human-friendly field name
                        'label': "# Volumes",
                        # Look up the 'id' in the latest object.
                        'from': "latest",
                        # Priorities over 10 are hidden, lower is earlier in the list.
                        'priority': 0.1,
                    },
                },
            },
        })

        # Send the headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()

        # Send the body
        self.wfile.write(body)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def delete_socket_file():
    if os.path.exists(PLUGIN_UNIX_SOCK):
        os.remove(PLUGIN_UNIX_SOCK)

def sig_handler(b, a):
    delete_socket_file()
    exit(0)

def main():
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    start_update_loop()

    # Ensure the socket directory exists
    mkdir_p(os.path.dirname(PLUGIN_UNIX_SOCK))
    # Remove existing socket in case it was left behind
    delete_socket_file()
    # Listen for connections on the unix socket
    server = socketserver.UnixStreamServer(PLUGIN_UNIX_SOCK, Handler)
    try:
        server.serve_forever()
    except:
        delete_socket_file()
        raise

main()
