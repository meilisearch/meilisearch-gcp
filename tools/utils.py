import datetime
import time
import sys
import requests
import googleapiclient.discovery

import config as conf

STATUS_OK = 0
STATUS_TIMEOUT = 1
STATUS_ERROR = 2

# INSTANCE


def wait_for_instance_running(project, zone, timeout_seconds=None):
    compute = googleapiclient.discovery.build('compute', 'v1')
    start_time = datetime.datetime.now()
    while timeout_seconds is None \
            or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
        instance = compute.instances().get(project=project, zone=zone,
                                           instance=conf.INSTANCE_BUILD_NAME).execute()
        if instance['status'] not in ['STAGING', 'PROVISIONING']:
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
            if resp.status_code >= 200 and resp.status_code < 300:
                return STATUS_OK
        except Exception:
            pass
        time.sleep(1)
    return STATUS_TIMEOUT


def wait_for_zone_operation(compute, project, zone, operation, timeout_seconds=None):
    start_time = datetime.datetime.now()
    while timeout_seconds is None \
            or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
        try:
            result = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation).execute()
            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return STATUS_OK
        except Exception as err:
            print(err)
        time.sleep(1)
    return STATUS_TIMEOUT


def wait_for_global_operation(compute, project, operation, timeout_seconds=None):
    start_time = datetime.datetime.now()
    while timeout_seconds is None \
            or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
        try:
            result = compute.globalOperations().get(
                project=project,
                operation=operation).execute()
            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return STATUS_OK
        except Exception as err:
            print(err)
        time.sleep(1)
    return STATUS_TIMEOUT


def terminate_instance_and_exit(compute, project, zone, instance):
    print('   Terminating instance {}'.format(instance.id))
    compute.instances().delete(
        project=project,
        zone=zone,
        instance=instance
    ).execute()
    print('ENDING PROCESS WITH EXIT CODE 1')
    sys.exit(1)

# BUILD AND PUBLISH


def wait_for_build_operation(cloudbuild, project, operation, timeout_seconds=None):
    start_time = datetime.datetime.now()
    while timeout_seconds is None \
            or check_timeout(start_time, timeout_seconds) is not STATUS_TIMEOUT:
        try:
            result = cloudbuild.projects().builds().get(
                projectId=project,
                id=operation
            ).execute()
        except Exception as err:
            print(err)
        if result['status'] == 'SUCCESS':
            return STATUS_OK
        if result['status'] == 'FAILURE':
            print(result)
            raise Exception('Error on build operation')
        time.sleep(1)
    return STATUS_TIMEOUT

# GENERAL


def check_timeout(start_time, timeout_seconds):
    elapsed_time = datetime.datetime.now() - start_time
    if elapsed_time.total_seconds() > timeout_seconds:
        return STATUS_TIMEOUT
    return STATUS_OK
