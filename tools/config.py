import requests
from datetime import datetime

# Update with the MeiliSearch version TAG you want to build the AMI with

MEILI_CLOUD_SCRIPTS_VERSION_TAG='v0.19.0'

### Setup environment and settings

SSH_USER='esk'

DEBIAN_BASE_IMAGE_FAMILY='ubuntu-2004-lts'
IMAGE_DESCRIPTION_NAME="MeiliSearch-{} running on {}".format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, DEBIAN_BASE_IMAGE_FAMILY)

USER_DATA =requests.get(
    'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{}/scripts/cloud-config.yaml'
    .format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
).text

SNAPSHOT_NAME="meilisearch-{}-{}".format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG,
    DEBIAN_BASE_IMAGE_FAMILY
    ).replace('.', '-')

INSTANCE_BUILD_NAME="{}-build-{}".format(SNAPSHOT_NAME, datetime.now().strftime("-%d-%m-%Y-%H-%M-%S"))


GCP_DEFAULT_PROJECT='meilisearchimage'
GCP_DEFAULT_ZONE='us-central1-a'


INSTANCE_TYPE='zones/{}/machineTypes/n1-standard-1'.format(GCP_DEFAULT_ZONE)

MEILISEARCH_LOGO_URL='https://github.com/meilisearch/integration-guides/blob/main/assets/logos/logo.svg'
