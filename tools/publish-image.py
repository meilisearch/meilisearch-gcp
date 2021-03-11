# Build image using projects.builds()
#
# https://cloud.google.com/compute/docs/images/export-image#exporting_an_image_with_a_single_command
# https://cloud.google.com/build/docs/api/reference/rest/v1/projects.builds

# Make image public

import googleapiclient.discovery

import config as conf

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
print(export_image)
