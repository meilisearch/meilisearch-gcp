from datetime import datetime
import requests

# Update with the Meilisearch version TAG you want to build the image with

MEILI_CLOUD_SCRIPTS_VERSION_TAG = 'v0.29.0'

# Update with the custom image name that you want to publish after TESTING

PUBLISH_IMAGE_NAME = 'meilisearch-v0-28-0-debian-10-build--18-07-2022-14-48-17'

# Setup environment and settings

DEBIAN_BASE_IMAGE_PROJECT = 'debian-cloud'
DEBIAN_BASE_IMAGE_FAMILY = 'debian-10'
IMAGE_DESCRIPTION_NAME = f'Meilisearch-{MEILI_CLOUD_SCRIPTS_VERSION_TAG} running on {DEBIAN_BASE_IMAGE_FAMILY}'
IMAGE_FORMAT = 'vmdk'
IMAGE_DESTINATION_URI = f'gs://meilisearch-image/meilisearch-{MEILI_CLOUD_SCRIPTS_VERSION_TAG}-{DEBIAN_BASE_IMAGE_FAMILY}.{IMAGE_FORMAT}'
IMAGE_DESTINATION_BUCKET_NAME = 'meilisearch-image'
SERVICE_ACCOUNT_EMAIL = '591812945139@cloudbuild.gserviceaccount.com'

USER_DATA = requests.get(
    f'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{MEILI_CLOUD_SCRIPTS_VERSION_TAG}/scripts/providers/gcp/cloud-config.yaml'
).text

SNAPSHOT_NAME = f'meilisearch-{MEILI_CLOUD_SCRIPTS_VERSION_TAG}-{DEBIAN_BASE_IMAGE_FAMILY}'.replace('.', '-')

INSTANCE_BUILD_NAME = f"{SNAPSHOT_NAME}-build-{datetime.now().strftime('-%d-%m-%Y-%H-%M-%S')}"

GCP_DEFAULT_PROJECT = 'meilisearchimage'
GCP_DEFAULT_ZONE = 'us-central1-a'

INSTANCE_TYPE = f'zones/{GCP_DEFAULT_ZONE}/machineTypes/n1-standard-1'

MEILISEARCH_LOGO_URL = 'https://github.com/meilisearch/integration-guides/blob/main/assets/logos/logo.svg'

# SEE: https://blog.woohoosvcs.com/2019/11/cloud-init-on-google-compute-engine/
STARTUP_SCRIPT = """
#!/bin/bash

if ! type cloud-init > /dev/null 2>&1 ; then
  echo "Ran - `date`" >> /root/startup
  sleep 30
  apt install -y cloud-init

  if [ $? == 0 ]; then
    echo "Ran - Success - `date`" >> /root/startup
    systemctl enable cloud-init
  else
    echo "Ran - Fail - `date`" >> /root/startup
  fi

  # Reboot either way
  reboot
fi
"""

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
    'tags': {
        'items': [
            'http-server',
            'https-server'
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
                'key': 'startup-script',
                'value': STARTUP_SCRIPT
            },
            {
                'key': 'block-project-ssh-keys',
                'value': False
            }
        ]
    }
}

# DOCS: https://cloud.google.com/compute/docs/reference/rest/v1/instances/insert
BUILD_INSTANCE_TEST_CONFIG = {
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
    'tags': {
        'items': [
            'http-server',
            'https-server'
        ],
    },
    'networkInterfaces': [{
        'network': 'global/networks/default',
        'accessConfigs': [
            {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
        ]
    }],
    'metadata': {
        'items': [
            {
                'key': 'block-project-ssh-keys',
                'value': False
            }
        ]
    }
}

EXPORT_IMAGE_CONFIG = {
    'steps': [
        {
            'args': [
                '-timeout=7000s',
                f'-source_image={PUBLISH_IMAGE_NAME}',
                '-client_id=api',
                f'-format={IMAGE_FORMAT}',
                f'-destination_uri={IMAGE_DESTINATION_URI}',
                f'-compute_service_account={SERVICE_ACCOUNT_EMAIL}'
            ],
            'name':'gcr.io/compute-image-tools/gce_vm_image_export:release',
            'env':[
                'BUILD_ID=$BUILD_ID'
            ]
        }
    ]
}
