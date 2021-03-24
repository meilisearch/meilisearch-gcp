import requests
from datetime import datetime

# Update with the MeiliSearch version TAG you want to build the image with

MEILI_CLOUD_SCRIPTS_VERSION_TAG = 'v0.19.0'

# Update with the custom image name that you want to publish after TESTING

PUBLISH_IMAGE_NAME = 'meilisearch-v0-19-0-ubuntu-2004-lts-build--15-03-2021-19-10-42'

# Update with the username present in the SSH key added to gcp Compute Engine platform
#
# https://console.cloud.google.com/compute/metadata/sshKeys?project=meilisearchimage&authuser=1&folder&organizationId=710828868196

SSH_USER = 'esk'

# Setup environment and settings

DEBIAN_BASE_IMAGE_FAMILY = 'ubuntu-2004-lts'

IMAGE_DESCRIPTION_NAME = "MeiliSearch-{} running on {}".format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG, DEBIAN_BASE_IMAGE_FAMILY)
IMAGE_FORMAT = 'vmdk'
IMAGE_DESTINATION_URI = 'gs://meilisearch-image/meilisearch-{}-{}.{}'.format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG, DEBIAN_BASE_IMAGE_FAMILY, IMAGE_FORMAT)
IMAGE_DESTINATION_BUCKET_NAME = 'meilisearch-image'
SERVICE_ACCOUNT_EMAIL = '591812945139-compute@developer.gserviceaccount.com'

USER_DATA = requests.get(
    'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{}/scripts/cloud-config.yaml'
    .format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
).text

SNAPSHOT_NAME = "meilisearch-{}-{}".format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG,
    DEBIAN_BASE_IMAGE_FAMILY
).replace('.', '-')

INSTANCE_BUILD_NAME = "{}-build-{}".format(
    SNAPSHOT_NAME, datetime.now().strftime("-%d-%m-%Y-%H-%M-%S"))

GCP_DEFAULT_PROJECT = 'meilisearchimage'
GCP_DEFAULT_ZONE = 'us-central1-a'

INSTANCE_TYPE = 'zones/{}/machineTypes/n1-standard-1'.format(GCP_DEFAULT_ZONE)

MEILISEARCH_LOGO_URL = 'https://github.com/meilisearch/integration-guides/blob/main/assets/logos/logo.svg'

# DOCS: https://cloud.google.com/compute/docs/reference/rest/v1/instances/insert
BUILD_INSTANCE_CONFIG = {
    'name': INSTANCE_BUILD_NAME,
    'machineType': INSTANCE_TYPE,
    'disks': [
        {
            'boot': True,
            'autoDelete': True,
            'initializeParams': {
                'sourceImage': '',
            }
        }
    ],
    "tags": {
        "items": [
            "http-server",
            "https-server"
        ],
    },
    'networkInterfaces': [{
        'network': 'global/networks/default',
        'accessConfigs': [
            {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
        ]
    }],
    # user-data
    'metadata': {
        'items': [
            {
                'key': 'user-data',
                'value': USER_DATA,
            },
            {
                "key": "block-project-ssh-keys",
                "value": False
            }
        ]
    }
}

EXPORT_IMAGE_CONFIG = {
    'steps': [
        {
            'args': [
                '-timeout=7000s',
                '-source_image={}'.format(PUBLISH_IMAGE_NAME),
                '-client_id=api',
                '-format={}'.format(IMAGE_FORMAT),
                '-destination_uri={}'.format(IMAGE_DESTINATION_URI),
                '-compute_service_account={}'.format(SERVICE_ACCOUNT_EMAIL)
            ],
            'name':'gcr.io/compute-image-tools/gce_vm_image_export:release',
            'env':[
                'BUILD_ID=$BUILD_ID'
            ]
        }
    ]
}
