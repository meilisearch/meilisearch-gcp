import datetime
import time
import sys
import googleapiclient.discovery
import config as conf
import utils

compute = googleapiclient.discovery.build('compute', 'v1')

if len(sys.argv) > 1:
    SNAPSHOT_NAME = sys.argv[1]
else:
    raise Exception('No snapshot name specified')

print(f'Running test for image named: {SNAPSHOT_NAME}...')

# Get the image for the test

source_image = compute.images().get(project=conf.GCP_DEFAULT_PROJECT,
                                    image=SNAPSHOT_NAME).execute()

# Create GCP Compute instance to test Meilisearch image

print('Creating GCP Compute instance')

instance_config = conf.BUILD_INSTANCE_TEST_CONFIG
instance_config['disks'][0]['initializeParams']['sourceImage'] = source_image['selfLink']

create = compute.instances().insert(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    body=instance_config).execute()
print(f'   Instance created. Name: {conf.INSTANCE_BUILD_NAME}')

# Wait for GCP instance to be 'RUNNING'

print('Waiting for GCP Compute instance state to be "RUNNING"')
state_code, state, instance = utils.wait_for_instance_running(
    conf.GCP_DEFAULT_PROJECT, conf.GCP_DEFAULT_ZONE, timeout_seconds=600)
print(f'   Instance state: {state}')

if state_code == utils.STATUS_OK:
    instance_ip = instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    print(f'   Instance IP: {instance_ip}')
else:
    print(f'   Error: {state_code}. State: {state}.')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

# Wait for Health check after configuration is finished

print('Waiting for Meilisearch health check (may take a few minutes: config and reboot)')
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
    print(f'   Exception: {err}')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )
print('   Version of Meilisearch match!')

# Stop instance

print('Stopping GCP instance...')

TIMEOUT_SECONDS=60
start_time = datetime.datetime.now()
IS_TIMEOUT=0
while IS_TIMEOUT is utils.STATUS_OK:
    try:
        print('Trying to stop instance ...')
        stop_instance_operation = compute.instances().stop(
            project=conf.GCP_DEFAULT_PROJECT,
            zone=conf.GCP_DEFAULT_ZONE,
            instance=conf.INSTANCE_BUILD_NAME
        ).execute()
        break
    except Exception as err:
        print(f'   Exception: {err}')
    time.sleep(1)
    IS_TIMEOUT=utils.check_timeout(start_time, TIMEOUT_SECONDS)
if IS_TIMEOUT is not utils.STATUS_OK:
    print('Timeout when trying to stop the instance')
    utils.terminate_instance_and_exit(
        compute=compute,
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        instance=conf.INSTANCE_BUILD_NAME
    )

print('Successfully stopped instance')

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

# Delete instance

print('Delete instance...')
compute.instances().delete(
    project=conf.GCP_DEFAULT_PROJECT,
    zone=conf.GCP_DEFAULT_ZONE,
    instance=conf.INSTANCE_BUILD_NAME
).execute()
print('Instance deleted')
