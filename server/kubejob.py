import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import yaml
from jinja2 import Template
import uuid

logger = logging.getLogger(__name__)

config.load_incluster_config()
configuration = client.Configuration()
api_batch_v1 = client.BatchV1Api(client.ApiClient(configuration))
api_v1 = client.CoreV1Api(client.ApiClient(configuration))

def test_credentials():
    api_response = {'message': 'ERROR: Failure connecting to Kubernetes API server'}
    try:
        api_response = api_v1.get_api_resources()
        logging.info(api_response)
        api_response = {'message': 'Success connecting to Kubernetes API server'}
    except ApiException as e:
        print("Exception when calling API: {}\n".format(e))
    return api_response


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


def create_job():
    try:
        namespace = get_namespace()
        with open(os.path.join(os.path.dirname(__file__), "job.tpl.yaml")) as f:
            templateText = f.read()
        template = Template(templateText)
        job_body = yaml.safe_load(template.render(
            name='test-job-{}'.format(generate_uuid()),
            namespace=namespace,
            backoffLimit=2,
            container_name='test-job-container',
            image='hello-world',
            # command=input["command"],
        ))
        api_response = api_batch_v1.create_namespaced_job(
            namespace=namespace, body=job_body
        )
        # logger.info("Job {} created".format(input["configjob"]["metadata"]["jobId"]))
    except ApiException as e:
        msg = "Exception when calling BatchV1Api->create_namespaced_job: {}\n".format(e)
        logger.error(msg)
        api_response = {
            'message': msg
        }
    return api_response
