import requests
import os
import string
import random
import subprocess

from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
from google.cloud import compute_v1

app = Flask(__name__)

PORT = 8000
GCP_PROJECT_ID = 'hackathon-project-383908'
GCP_ZONE = 'us-central1-a'
GCP_INSTANCES_CLIENT = compute_v1.InstancesClient()
GCP_IMAGES_CLIENT = compute_v1.ImagesClient()
GCP_ZONEOPS_CLIENT = compute_v1.ZoneOperationsClient()

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
    instances = GCP_INSTANCES_CLIENT.list(project=GCP_PROJECT_ID, zone=GCP_ZONE)
    print(instances)
    instances_name = []
    for instance in instances:
        print(instance.name)
        instances_name.append(instance.name)
    return {'instances': instances_name}

@app.route('/create-compute-instance', methods=['POST'])
def create_compute_instance():
    image_project = 'debian-cloud'
    image_family = 'debian-10'
    image_response = GCP_IMAGES_CLIENT.get_from_family(project=image_project, family=image_family)
    source_disk_image = image_response.self_link
    instance_name = request.json['instance_name']
    machine_type = 'https://www.googleapis.com/compute/v1/projects/%s/zones/%s/machineTypes/e2-micro' % (GCP_PROJECT_ID, GCP_ZONE)
    instance_config = {
        'name': instance_name,
        'machine_type': machine_type,
        'disks': [{
            'initialize_params': {
                'source_image': source_disk_image
            },
            'boot': True,
            'auto_delete': True
        }],
        'network_interfaces': [{
            'access_configs': [{
                'name': 'External NAT'
            }],
            'network': 'global/networks/default'
        }]
    }
    print(instance_config)
    operation = GCP_INSTANCES_CLIENT.insert(project=GCP_PROJECT_ID, zone=GCP_ZONE, instance_resource=instance_config)
    # Wait for the operation to complete
    GCP_ZONEOPS_CLIENT.wait(project=GCP_PROJECT_ID, zone=GCP_ZONE, operation=operation.name)

    instance_url = 'https://console.cloud.google.com/compute/instancesDetail/zones/%s/instances/%s?project=%s&authuser=1' % (GCP_ZONE, instance_name, GCP_PROJECT_ID)
    print(instance_url)

    return {'instance_url': instance_url}

@app.route('/configure-compute-instance', methods=['POST'])
def configure_compute_instance():
    print(request.json)
    instance_name = request.json['instance_name']
    commands = request.json['commands']
    for command in commands:
        gcloud_command = ['gcloud', 'compute', 'ssh', instance_name, '--zone', GCP_ZONE, '--command', command]
        print(gcloud_command)

        result = subprocess.run(gcloud_command, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return {'message': result.stderr}, 400

    return {}

@app.route('/visualize-setup')
def visualize_setup():
    return {'visualization_url': 'https://youtu.be/dQw4w9WgXcQ'}


if __name__ == '__main__':
    app.run(port=PORT, debug=True)
