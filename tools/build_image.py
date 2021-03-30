import googleapiclient.discovery
import config as conf
import utils

compute = googleapiclient.discovery.build('compute', 'v1')

# Create GCP Compute instance to setup MeiliSearch

print('Creating GCP Compute instance')

source_image = compute.images().getFromFamily(
    project='ubuntu-os-cloud',
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

print('Triggering MeiliSearch GCP Snapshot creation...')
create_image_operation = compute.images().insert(
    project=conf.GCP_DEFAULT_PROJECT,
    body={
        'name': conf.INSTANCE_BUILD_NAME,
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
