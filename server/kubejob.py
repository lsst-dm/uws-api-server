import globals
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import yaml
from jinja2 import Template
import uuid

# Configure logging
log = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
try:
    log.setLevel(os.environ['LOG_LEVEL'].upper())
except:
    log.setLevel('WARNING')

config.load_incluster_config()
configuration = client.Configuration()
api_batch_v1 = client.BatchV1Api(client.ApiClient(configuration))
api_v1 = client.CoreV1Api(client.ApiClient(configuration))

def get_namespace():
    # When running in a pod, the namespace should be determined automatically,
    # otherwise we assume the local development is in the default namespace
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as file:
            namespace = file.read().replace('\n', '')
    except:
        try:
            namespace = os.environ['NAMESPACE']
        except:
            namespace = 'default'
    return namespace


def generate_uuid():
    return str(uuid.uuid4()).replace("-", "")


def get_job_name_from_id(job_id):
    return 'uws-job-{}'.format(job_id)


def create_job(command, workdir, replicas=1, environment=None):
    response = {
        'job_id': None,
        'api_response': None,
        'message': None,
        'status': globals.STATUS_OK,
    }
    try:
        namespace = get_namespace()
        job_id = generate_uuid()
        job_name = get_job_name_from_id(job_id)
        with open(os.path.join(os.path.dirname(__file__), "job.tpl.yaml")) as f:
            templateText = f.read()
        template = Template(templateText)
        job_body = yaml.safe_load(template.render(
            name=job_name,
            jobId=job_id,
            namespace=namespace,
            backoffLimit=2,
            replicas=replicas,
            container_name='uws-job',
            image='lsstsqre/centos:d_latest',
            command=["/bin/bash", "-c", '''cd {} && {}'''.format(workdir, command)],
            environment=environment,
        ))
        log.debug("Job {}:\n{}".format(job_name, yaml.dump(job_body, indent=2)))
        api_response = api_batch_v1.create_namespaced_job(
            namespace=namespace, body=job_body
        )
        response['job_id'] = job_id
        response['api_response'] = api_response
        log.debug(f"Job {job_name} created")
    # TODO: Is there additional information to obtain from the ApiException?
    # except ApiException as e:
    #     msg = str(e)
    #     log.error(msg)
    #     response['status'] = globals.STATUS_ERROR
    #     response['message'] = msg
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['message'] = msg
        response['status'] = globals.STATUS_ERROR
    return response


def list_jobs(phase=None):
    jobs = []
    response = {
        'jobs': jobs,
        'status': globals.STATUS_OK,
        'message': '',
    }
    try:
        namespace = get_namespace()
        # job_name = get_job_name_from_id
        api_response = api_batch_v1.list_namespaced_job(
            namespace=namespace, 
        )
        # Assume only one job is in the list
        for item in api_response.items:
            jobs.append({
                'name': item.metadata.name,
                'creation_time': item.metadata.creation_timestamp,
                'job_id': item.metadata.labels['jobId'],
                'command': item.spec.template.spec.containers[0].command,
                'status': {
                    'active': True if item.status.active else False,
                    'start_time': item.status.start_time,
                    'completion_time': item.status.completion_time,
                    'succeeded': True if item.status.succeeded else False,
                    'failed': True if item.status.failed else False,
                },
            })
        response['jobs'] = jobs
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['status'] = globals.STATUS_ERROR
        response['message'] = msg
    return response
    
def list_job(job_id):
    response = {
        'name': None,
        'creation_time': None,
        'job_id': job_id,
        'command': None,
        'status': {
            'active': None,
            'start_time': None,
            'completion_time': None,
            'succeeded': None,
            'failed': None,
        },
        'message': '',
        'error_code': globals.HTTP_NOT_FOUND,
    }
    try:
        namespace = get_namespace()
        # job_name = get_job_name_from_id
        api_response = api_batch_v1.list_namespaced_job(
            namespace=namespace, 
            label_selector=f'jobId={job_id}'
        )
        # Assume only one job is in the list
        for item in api_response.items:
            response = {
                'name': item.metadata.name,
                'creation_time': item.metadata.creation_timestamp,
                'job_id': item.metadata.labels['jobId'],
                'command': item.spec.template.spec.containers[0].command,
                'status': {
                    'active': True if item.status.active else False,
                    'start_time': item.status.start_time,
                    'completion_time': item.status.completion_time,
                    'succeeded': True if item.status.succeeded else False,
                    'failed': True if item.status.failed else False,
                },
                'message': '',
                'error_code': globals.HTTP_OK,
            }
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['error_code'] = globals.HTTP_SERVER_ERROR
        response['message'] = msg
    return response

def delete_job(job_id):
    response = {
        'status': globals.STATUS_OK,
        'message': '',
        'code': globals.HTTP_OK,
    }
    try:
        namespace = get_namespace()
        job_name = get_job_name_from_id(job_id)
        api_response = api_batch_v1.delete_namespaced_job(
            namespace=namespace, 
            name=job_name,
        )
        response['status']  = api_response.status if api_response.status else response['status']
        response['message'] = api_response.status if api_response.message else response['message']
        response['code']    = api_response.status if api_response.code else response['code']
        response['message'] = api_response.status if api_response.message else response['message']
    except ApiException as e:
        msg = str(e)
        response['message'] = msg 
        if msg.startswith('(404)'):
            response['code'] = 404
        else:
            response['status'] = globals.STATUS_ERROR
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['status'] = globals.STATUS_ERROR
        response['message'] = msg
    return response
