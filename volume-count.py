#!/usr/bin/env python

from docker import Client
import BaseHTTPServer
import SocketServer
import datetime
import errno
import json
import os
import signal
import socket
import threading
import time
import urllib2
import collections
from kubetool import KubeTool
from urllib.parse import urlparse

PLUGIN_ID="test_plugin"
PLUGIN_UNIX_SOCK="/var/run/scope/plugins/" + PLUGIN_ID + ".sock"
DOCKER_SOCK="unix://var/run/docker.sock"
KubeInstance = KubeTool()


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
        for container_id, test_plugin in container_volume_counts().iteritems():
            new["%s;<container>" % (container_id)] = {
                'latest': {
                    'volume_count': {
                        'timestamp': timestamp,
                        'value': str(test_plugin),
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
    cli = Client(base_url=DOCKER_SOCK, version='auto')
    for c in cli.containers(all=True):
        containers[c['Id']] = len(c['Mounts'])
    return containers


# class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
#     def do_GET(self):
#         # The logger requires a client_address, but unix sockets don't have
#         # one, so we fake it.
#         self.client_address = "-"

#         # Generate our json body
#         body = json.dumps({
#             'Plugins': [
#                 {
#                     'id': PLUGIN_ID,
#                     'label': 'Test Plugins',
#                     'description': 'Shows how many volumes each container has mounted',
#                     'interfaces': ['reporter'],
#                     'api_version': '1',
#                 }
#             ],
#             'Container': {
#                 'nodes': nodes,
#                 # Templates tell the UI how to render this field.
#                 'metadata_templates': {
#                     'test_plugin': {
#                         # Key where this data can be found.
#                         'id': "test_plugin",
#                         # Human-friendly field name
#                         'label': "# Volumes",
#                         # Look up the 'id' in the latest object.
#                         'from': "latest",
#                         # Priorities over 10 are hidden, lower is earlier in the list.
#                         'priority': 0.1,
#                     },
#                 },
#             },
#         })

#         # Send the headers
#         self.send_response(200)
#         self.send_header('Content-Type', 'application/json')
#         self.send_header('Content-Length', len(body))
#         self.end_headers()

#         # Send the body
#         self.wfile.write(body)

# def mkdir_p(path):
#     try:
#         os.makedirs(path)
#     except OSError as exc:
#         if exc.errno == errno.EEXIST and os.path.isdir(path):
#             pass
#         else:
#             raise

# def delete_socket_file():
#     if os.path.exists(PLUGIN_UNIX_SOCK):
#         os.remove(PLUGIN_UNIX_SOCK)

# def sig_handler(b, a):
#     delete_socket_file()
#     exit(0)

# def main():
#     signal.signal(signal.SIGTERM, sig_handler)
#     signal.signal(signal.SIGINT, sig_handler)

#     start_update_loop()

#     # Ensure the socket directory exists
#     mkdir_p(os.path.dirname(PLUGIN_UNIX_SOCK))
#     # Remove existing socket in case it was left behind
#     delete_socket_file()
#     # Listen for connections on the unix socket
#     server = SocketServer.UnixStreamServer(PLUGIN_UNIX_SOCK, Handler)
#     try:
#         server.serve_forever()
#     except:
#         delete_socket_file()
#         raise

# main()
#print(KubeInstance.read_pod_log("kube-system","kube-scheduler-minikube"))


class PluginRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, **kwargs):
        self.request_log = ''
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_GET(self):
        self.log_extra = ''
        path = urlparse(self.path)[2].lower()
        if path == '/report':
            self.do_report()
        else:
            self.send_response(404)
            self.send_header('Content-length', 0)
            self.end_headers()

    def do_report(self):
        

        metric_templates = collections.defaultdict(dict)
        priority = 0.1
        metric_templates['test_plugin'] = {
                        'id':       'test_plugin',
                        'label':    'Useful Info about xApps',
                        'priority': priority,
        }
        
        report = {
        'Process': {
                'nodes': process_nodes,
                'metric_templates': metric_templates,
                },
        'Plugins': [
                {
                'id': PLUGIN_ID,
                'label': 'Test Plugins',
                'description': 'For testing weave plugin',
                'interfaces': ['reporter'],
                'api_version': '1',
                }
            ]
        }
        body = json.dumps(report)
