import sys
import googleapiclient.discovery
import config as conf
import utils

compute = googleapiclient.discovery.build('compute', 'v1')

# Remove analytics for CI jobs

if len(sys.argv) > 1 and '--no-analytics' in sys.argv:
    print('Launch build image without analytics.')
    config = conf.BUILD_INSTANCE_CONFIG.get('metadata').get('items')[0].get('value')
    test = conf.BUILD_INSTANCE_CONFIG['metadata']['items'][0]['value']
    if '--env development' in conf.BUILD_INSTANCE_CONFIG['metadata']['items'][0]['value']:
        index = conf.BUILD_INSTANCE_CONFIG['metadata']['items'][0]['value'].find('--env development')
        conf.BUILD_INSTANCE_CONFIG['metadata']['items'][0]['value'] = conf.BUILD_INSTANCE_CONFIG['metadata']['items'][0]['value'][:index] + '--no-analytics=true ' + conf.BUILD_INSTANCE_CONFIG['metadata']['items'][0]['value'][index:]

# Create GCP Compute instance to setup MeiliSearch

print('Creating GCP Compute instance')

source_image = compute.images().getFromFamily(
    project=conf.DEBIAN_BASE_IMAGE_PROJECT,
    family=conf.DEBIAN_BASE_IMAGE_FAMILY
).execute()

instance_config = conf.BUILD_INSTANCE_CONFIG
instance_config['disks'][0]['initializeParams']['sourceImage'] = source_image['selfLink']

create = compute.instances().insert(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    body=instance_config).execute()
print('   Instance created. Name: {}'.format(conf.INSTANCE_BUILD_NAME))


# Wait for GCP instance to be 'RUNNING'

print('Waiting for GCP Compute instance state to be "RUNNING"')
state_code, state = utils.wait_for_instance_running(
    conf.GCP_DEFAULT_PROJECT, conf.GCP_DEFAULT_ZONE, timeout_seconds=600)
print('   Instance state: {}'.format(state))

if state_code == utils.STATUS_OK:
    instance = compute.instances().get(project=conf.GCP_DEFAULT_PROJECT,
                                       zone=conf.GCP_DEFAULT_ZONE, instance=conf.INSTANCE_BUILD_NAME).execute()
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

# Wait for Health check after configuration is finished

print('Waiting for MeiliSearch health check (may take a few minutes: config and reboot)')
HEALTH = utils.wait_for_health_check(instance_ip, timeout_seconds=600)
if HEALTH == utils.STATUS_OK:
    print('   Instance is healthy')
else:
    print('   Timeout waiting for health check')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

# Check version

print('Waiting for Version check')
try:
    utils.check_meilisearch_version(
        instance_ip, conf.MEILI_CLOUD_SCRIPTS_VERSION_TAG)
except Exception as err:
    print("   Exception: {}".format(err))
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )
print('   Version of meilisearch match!')

# Stop instance before image creation

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

STOPPED = utils.wait_for_zone_operation(
    compute=compute,
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    operation=stop_instance_operation['name']
)
if STOPPED == utils.STATUS_OK:
    print('   Instance stopped')
else:
    print('   Timeout waiting for instace stop operation')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

# Create GCP Snapshot

if len(sys.argv) > 1 and sys.argv[1] != '--no-analytics':
    SNAPSHOT_NAME = sys.argv[1]
else:
    SNAPSHOT_NAME = conf.INSTANCE_BUILD_NAME

print('Triggering MeiliSearch GCP Snapshot creation...')
create_image_operation = compute.images().insert(
    project=conf.GCP_DEFAULT_PROJECT,
    body={
        'name': SNAPSHOT_NAME,
        'sourceDisk': instance['disks'][0]['source'],
        'description': conf.IMAGE_DESCRIPTION_NAME,
    }
).execute()

IMAGE_CREATION = utils.wait_for_global_operation(
    compute=compute,
    project=conf.GCP_DEFAULT_PROJECT,
    operation=create_image_operation['name']
)
if IMAGE_CREATION == utils.STATUS_OK:
    print('   Image created')
else:
    print('   Timeout waiting for image creation')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

# Delete instance

print('Delete instance...')
compute.instances().delete(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    instance=conf.INSTANCE_BUILD_NAME
).execute()
print('Instance deleted')
