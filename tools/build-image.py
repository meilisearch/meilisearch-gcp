import googleapiclient.discovery

import config as conf

compute = googleapiclient.discovery.build('compute', 'v1')

### Create EC2 instance to setup MeiliSearch

print('Creating GCP Compute instance')

source_image = compute.images().getFromFamily(
    project='ubuntu-os-cloud',
    family=conf.DEBIAN_BASE_IMAGE_FAMILY
).execute()['selfLink']
print(source_image)

# DOCS: https://cloud.google.com/compute/docs/reference/rest/v1/instances/insert
config = {
        'name': conf.INSTANCE_BUILD_NAME,
        'machineType': conf.INSTANCE_TYPE,
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_image,
                }
            }
        ],
        "tags": {
            "items": [
                "http-server",
                "https-server"
            ],
  },

        # Specify a network interface with NAT to access the public
        # internet.
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],

        #user-data
        'metadata': {
            'items': [
                {
                    'key': 'user-data',
                    'value': conf.USER_DATA,
                }
            ]
        }

    }

resp = compute.instances().insert(
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        body=config).execute()

print(resp)
