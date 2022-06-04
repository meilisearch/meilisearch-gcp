# Build image using projects.builds()
#
# https://cloud.google.com/compute/docs/images/export-image#exporting_an_image_with_a_single_command
# https://cloud.google.com/build/docs/api/reference/rest/v1/projects.builds

# Export image to bucket

import googleapiclient.discovery
from google.cloud import storage

import config as conf
import utils

cloudbuild = googleapiclient.discovery.build('cloudbuild', 'v1')
compute = googleapiclient.discovery.build('compute', 'v1')

export_image = cloudbuild.projects().builds().create(
    projectId='meilisearchimage',
    body=conf.EXPORT_IMAGE_CONFIG
).execute()

print('Waiting for image export operation')
IMAGE_EXPORT_OPERATION = utils.wait_for_build_operation(
    cloudbuild=cloudbuild,
    project=conf.GCP_DEFAULT_PROJECT,
    operation=export_image['metadata']['build']['id']
)
if IMAGE_EXPORT_OPERATION == utils.STATUS_OK:
    print(f'   Image exported: {conf.IMAGE_DESTINATION_URI}')
else:
    print('   Timeout waiting for image export')

# Make image public

print('Publishing image')
bucket = storage.Client().get_bucket(conf.IMAGE_DESTINATION_BUCKET_NAME)
policy = bucket.get_iam_policy(requested_policy_version=3)
policy.bindings.append(
    {'role': 'roles/storage.objectViewer', 'members': {'allUsers'}})
bucket.set_iam_policy(policy)
print('   Image is now public')

# Delete custom image

delete_image_operation = compute.images().delete(
    project=conf.GCP_DEFAULT_PROJECT,
    image=conf.PUBLISH_IMAGE_NAME
).execute()
