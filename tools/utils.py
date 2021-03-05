import datetime
import requests
import time
import googleapiclient.discovery

import config as conf

STATUS_OK=0
STATUS_TIMEOUT=1
STATUS_ERROR=2

### INSTANCE

def wait_for_instance_running(project, zone, timeout_seconds=None):
    compute = googleapiclient.discovery.build('compute', 'v1')
    start_time = datetime.datetime.now()
    while timeout_seconds is None \
        or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
        instance = compute.instances().get(project = project, zone=zone, instance=conf.INSTANCE_BUILD_NAME).execute()
        if instance['status'] not in ['STAGING','PROVISIONING']:
            if instance['status'] == 'RUNNING':
                return STATUS_OK, instance['status']
            return STATUS_ERROR, instance['status']
        time.sleep(1)
    return STATUS_TIMEOUT, None

def wait_for_health_check(instance_ip, timeout_seconds=None):
    start_time = datetime.datetime.now()
    while timeout_seconds is None \
        or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
        try:
            resp = requests.get('http://{}/health'.format(instance_ip))
            if resp.status_code >=200 and resp.status_code < 300:
                return STATUS_OK
        except Exception as e:
                pass
        time.sleep(1)
    return STATUS_TIMEOUT 

# def terminate_instance_and_exit(instance):
#     print('   Terminating instance {}'.format(instance.id))
#     instance.terminate()
#     print('ENDING PROCESS WITH EXIT CODE 1')
#     exit(1)

# ### AMI

# def wait_for_ami_available(image_id, region, timeout_seconds=None):
#     ec2 = boto3.resource('ec2', region)
#     start_time = datetime.datetime.now()
#     while timeout_seconds is None \
#         or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
#         ami  = ec2.Image(image_id)
#         if ami.state != 'pending':
#             if ami.state == 'available':
#                 return STATUS_OK, ami
#             return STATUS_ERROR, ami
#         time.sleep(1)
#     return STATUS_TIMEOUT, None

# def make_ami_public(image_id, region, timeout_seconds=None):
#     ec2 = boto3.resource('ec2', region)
#     start_time = datetime.datetime.now()
#     while timeout_seconds is None \
#         or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
#         ami  = ec2.Image(image_id)
#         ami.modify_attribute(
#             LaunchPermission={
#                 'Add': [{'Group': 'all'}]
#             }
#         )
#         if ami.public:
#             return STATUS_OK, ami.public
#         time.sleep(1)
#     return STATUS_TIMEOUT, None

### GENERAL

def check_timeout(start_time, timeout_seconds):
    elapsed_time = datetime.datetime.now() - start_time
    if elapsed_time.total_seconds() > timeout_seconds:
        return STATUS_TIMEOUT
    return STATUS_OK
