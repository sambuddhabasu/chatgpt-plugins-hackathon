import requests
import os

from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
from google.cloud import compute_v1

app = Flask(__name__)

PORT = 8000
GCP_PROJECT_ID = 'hackathon-project-383908'
GCP_ZONE = 'us-central1-a'
GCP_CLIENT = compute_v1.InstancesClient()

# Note: Setting CORS to allow chat.openapi.com is required for ChatGPT to access your plugin
CORS(app, origins=[f"http://localhost:{PORT}", "https://chat.openai.com"])


@app.route('/.well-known/ai-plugin.json')
def serve_manifest():
    return send_from_directory(os.path.dirname(__file__), 'ai-plugin.json')

@app.route('/logo.png')
def serve_logo():
    return send_from_directory(os.path.dirname(__file__), 'logo.png')

@app.route('/openapi.json')
def serve_openapi_json():
    return send_from_directory(os.path.dirname(__file__), 'openapi.json')

@app.route('/list-compute-instances')
def list_compute_instances():
    instances = GCP_CLIENT.list(project=GCP_PROJECT_ID, zone=GCP_ZONE)
    print(instances)
    instances_name = []
    for instance in instances:
        print(instance.name)
        instances_name.append(instance.name)
    return {'instances': instances_name}


if __name__ == '__main__':
    app.run(port=PORT, debug=True)
