from time import sleep
import googleapiclient.discovery
import os

import config as conf
import utils

compute = googleapiclient.discovery.build('compute', 'v1')
instance = None
instance_ip = None

### Create GCP Compute instance to setup MeiliSearch

print('Creating GCP Compute instance')

source_image = compute.images().getFromFamily(
    project='ubuntu-os-cloud',
    family=conf.DEBIAN_BASE_IMAGE_FAMILY
).execute()['selfLink']

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
            },
            {
                "key": "block-project-ssh-keys",
                "value": False
            }
        ]
    }
}
create = compute.instances().insert(
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        body=config).execute()
print('   Instance created. Name: {}'.format(conf.INSTANCE_BUILD_NAME))


### Wait for GCP instance to be 'RUNNING'

print('Waiting for GCP Compute instance state to be "RUNNING"')
state_code, state = utils.wait_for_instance_running(conf.GCP_DEFAULT_PROJECT, conf.GCP_DEFAULT_ZONE, timeout_seconds=600)
print('   Instance state: {}'.format(state))

if state_code == utils.STATUS_OK:
    instance = compute.instances().get(project = conf.GCP_DEFAULT_PROJECT, zone=conf.GCP_DEFAULT_ZONE, instance=conf.INSTANCE_BUILD_NAME).execute()
    instance_ip = instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    print('   Instance IP: {}'.format(instance_ip))
else:
    print('   Error: {}. State: {}.'.format(state_code, state))
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

### Wait for Health check after configuration is finished

print('Waiting for MeiliSearch health check (may take a few minutes: config and reboot)')
health = utils.wait_for_health_check(instance_ip, timeout_seconds=600)
if health == utils.STATUS_OK:
    print('   Instance is healthy')
else:
    print('   Timeout waiting for health check')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

### Execute deploy script via SSH

# Add your SSH KEY to https://console.cloud.google.com/compute/metadata/sshKeys
commands = [
    'curl https://raw.githubusercontent.com/meilisearch/cloud-scripts/{0}/scripts/deploy-meilisearch.sh | sudo bash -s {0} {1}'.format(conf.MEILI_CLOUD_SCRIPTS_VERSION_TAG, "GCP"),
]

for cmd in commands:
    ssh_command = 'ssh {user}@{host} -o StrictHostKeyChecking=no "{cmd}"'.format(
        user=conf.SSH_USER,
        host=instance_ip,
        cmd=cmd,
    )
    print("EXECUTE COMMAND:", ssh_command)
    os.system(ssh_command)
    sleep(5)

### Stop instance before image creation

print('Stopping GCP instance...')
instance = compute.instances().get(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    instance=conf.INSTANCE_BUILD_NAME
).execute()

stop_instance_operation = compute.instances().stop(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    instance=conf.INSTANCE_BUILD_NAME
).execute()

stopped = utils.wait_for_zone_operation(
    compute=compute, 
    project=conf.GCP_DEFAULT_PROJECT, 
    zone=conf.GCP_DEFAULT_ZONE, 
    operation=stop_instance_operation['name']
)
if stopped == utils.STATUS_OK:
    print('   Instance stopped')
else:
    print('   Timeout waiting for instace stop operation')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

### Create GCP Snapshot

print('Triggering MeiliSearch GCP Snapshot creation...')
create_image_operation = compute.images().insert(
    project=conf.GCP_DEFAULT_PROJECT,
    body={
        'name': conf.INSTANCE_BUILD_NAME,
        'sourceDisk': instance['disks'][0]['source'],
        'description': conf.IMAGE_DESCRIPTION_NAME,
    }
).execute()

image_creation = utils.wait_for_global_operation(
    compute=compute, 
    project=conf.GCP_DEFAULT_PROJECT, 
    operation=create_image_operation['name']
)
if image_creation == utils.STATUS_OK:
    print('   Image created')
else:
    print('   Timeout waiting for image creation')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

### Delete instance 

print("Delete instance...")
compute.instances().delete(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    instance=conf.INSTANCE_BUILD_NAME
).execute()
