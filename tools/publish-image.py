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

export_image = cloudbuild.projects().builds().create(
    projectId='meilisearchimage',
    body={
        'steps': [
            {
                'args':[
                    '-timeout=7000s',
                    '-source_image={}'.format(conf.PUBLISH_IMAGE_NAME),
                    '-client_id=api',
                    '-format={}'.format(conf.IMAGE_FORMAT),
                    '-destination_uri={}'.format(conf.IMAGE_DESTINATION_URI),
                    '-compute_service_account={}'.format(conf.SERVICE_ACCOUNT_EMAIL)
                ],
                'name':'gcr.io/compute-image-tools/gce_vm_image_export:release',
                'env':[
                    'BUILD_ID=$BUILD_ID'
                ]
            }
        ]
    }
).execute()

print("Waiting for image export operation")
image_export = utils.wait_for_build_operation(
    cloudbuild=cloudbuild, 
    project=conf.GCP_DEFAULT_PROJECT, 
    operation=export_image['metadata']['build']['id']
)
if image_export == utils.STATUS_OK:
    print('   Image exported: {}'.format(conf.IMAGE_DESTINATION_URI))
else:
    print('   Timeout waiting for image export')

# Make image public

print("Publishing image")
bucket = storage.Client().get_bucket(conf.IMAGE_DESTINATION_BUCKET_NAME)
policy = bucket.get_iam_policy(requested_policy_version=3)
policy.bindings.append({"role": 'roles/storage.objectViewer', "members": {'allUsers'}})
bucket.set_iam_policy(policy)
print("   Image is now public")

