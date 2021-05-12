import global_vars
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import shutil
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


def get_job_root_dir_from_id(job_id):
    return os.path.join(global_vars.UWS_ROOT_DIR, 'jobs', job_id)


def list_job_output_files(job_id):
    job_filepaths = []
    try:
        job_output_dir = os.path.join(get_job_root_dir_from_id(job_id), 'out')
        if os.path.isdir(job_output_dir):
            for dirpath, dirnames, filenames in os.walk(job_output_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if not filename.startswith('.') and os.path.isfile(filepath):
                        job_filepaths.append(filepath)
                        log.debug(filepath)
    except Exception as e:
        log.error(str(e))
        raise e
    return job_filepaths


def list_jobs(job_id=None):
    jobs = []
    response = {
        'jobs': jobs,
        'status': global_vars.STATUS_OK,
        'message': '',
    }
    try:
        namespace = get_namespace()
        if job_id:
            api_response = api_batch_v1.list_namespaced_job(
                namespace=namespace, 
                label_selector=f'jobId={job_id}',
            )
        else:
            api_response = api_batch_v1.list_namespaced_job(
                namespace=namespace, 
                label_selector=f'type=uws-job',
            )
        for item in api_response.items:
            envvars = []
            for envvar in item.spec.template.spec.containers[0].env:
                envvars.append({
                    'name': envvar.name,
                    'value': envvar.value,
                })
            job = {
                'name': item.metadata.name,
                'creation_time': item.metadata.creation_timestamp,
                'job_id': item.metadata.labels['jobId'],
                'run_id': item.metadata.labels['runId'],
                'command': item.spec.template.spec.containers[0].command,
                'environment': envvars,
                'output_files': list_job_output_files(item.metadata.labels['jobId']),
                'status': {
                    'active': True if item.status.active else False,
                    'start_time': item.status.start_time,
                    'completion_time': item.status.completion_time,
                    'succeeded': True if item.status.succeeded else False,
                    'failed': True if item.status.failed else False,
                },
            }
            jobs.append(job)
        response['jobs'] = jobs
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['status'] = global_vars.STATUS_ERROR
        response['message'] = msg
    return response


def delete_job(job_id):
    response = {
        'status': global_vars.STATUS_OK,
        'message': '',
        'code': global_vars.HTTP_OK,
    }
    try:
        namespace = get_namespace()
        job_name = get_job_name_from_id(job_id)
        api_response = api_batch_v1.delete_namespaced_job(
            namespace=namespace, 
            name=job_name,
        )
        response['status']  = api_response.status if api_response.status else response['status']
        response['message'] = api_response.message if api_response.message else response['message']
        response['code']    = api_response.code if api_response.code else response['code']
    except ApiException as e:
        msg = str(e)
        response['message'] = msg 
        if msg.startswith('(404)'):
            response['code'] = global_vars.HTTP_NOT_FOUND
        else:
            response['status'] = global_vars.STATUS_ERROR
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['status'] = global_vars.STATUS_ERROR
        response['message'] += f'\n\n{msg}'
    try:
        # Delete the job files if they exist
        job_root_dir = get_job_root_dir_from_id(job_id)
        if os.path.isdir(job_root_dir):
            log.debug(f'Deleting job files "{job_root_dir}"')
            shutil.rmtree(job_root_dir)
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['status'] = global_vars.STATUS_ERROR
        response['message'] += f'\n\n{msg}'
    return response


def create_job(command, run_id=None, url=None, commit_ref=None, replicas=1, environment=None):
    response = {
        'job_id': None,
        'api_response': None,
        'message': None,
        'status': global_vars.STATUS_OK,
    }
    try:
        namespace = get_namespace()
        job_id = generate_uuid()
        if not run_id:
            run_id = job_id
        job_name = get_job_name_from_id(job_id)
        job_root_dir = get_job_root_dir_from_id(job_id)
        job_output_dir = os.path.join(job_root_dir, 'out')
        if isinstance(url, str):
            # stripped_url = f'{url}'.strip('/').strip('.git').strip('/').strip()
            # hashed_url = hashlib.sha1(bytes(stripped_url, 'utf-8')).hexdigest()
            clone_dir = os.path.join(job_root_dir, 'src')
        else:
            clone_dir = None
        
        # Set environment-specific configuration for Job definition
        templateFile = "job.tpl.yaml"
        project_subpath = global_vars.PROJECT_SUBPATH
        image_tag = 'd_latest'
        # If targeting NCSA Integration cluster
        if global_vars.TARGET_CLUSTER == "int":
            # If PROJECT_SUBPATH is provided in the environment variables, use this to mount
            # the specified directory. Otherwise mount the subpath defined in the server's
            # env vars
            for envvar in environment:
                if envvar['name'] == 'PROJECT_SUBPATH':
                    project_subpath = envvar['value']
                if envvar['name'] == 'JOB_IMAGE_TAG':
                    image_tag = envvar['value']
            # If not a valid subdirectory of /project, return with error message
            assert os.path.isdir(f'/project/{project_subpath}')
        
        with open(os.path.join(os.path.dirname(__file__), templateFile)) as f:
            templateText = f.read()
        template = Template(templateText)
        job_body = yaml.safe_load(template.render(
            name=job_name,
            runId=run_id,
            jobId=job_id,
            namespace=namespace,
            backoffLimit=0,
            replicas=replicas,
            container_name='uws-job',
            # TODO: Allow some flexibility in the Docker container image name and/or tag.
            # CAUTION: Discrepancy between the UID of the image user and the UWS API server UID
            #          will create permissions problems. For example, if the job UID is 1001 and
            #          the server UID is 1000, then files created by the job will not in general 
            #          allow the server to delete them when cleaning up deleted jobs.
            image={
                'repository': 'lsstsqre/centos',
                'tag': image_tag,
            },
            command=command,
            environment=environment,
            url=url if url else '',
            clone_dir=clone_dir if clone_dir else '',
            commit_ref=commit_ref if commit_ref else '',
            uws_root_dir=global_vars.UWS_ROOT_DIR,
            target_cluster=global_vars.TARGET_CLUSTER,
            job_output_dir=job_output_dir,
            project_subpath=project_subpath,
            job_files_pvc=f'{os.environ["API_DOMAIN"]}-nfs-scratch-pvc',
            data_pvc=f'{os.environ["API_DOMAIN"]}-nfs-data-pvc',
            oods_comcam_pvc=f'{os.environ["API_DOMAIN"]}-nfs-oods-comcam-pvc',
            oods_auxtel_pvc=f'{os.environ["API_DOMAIN"]}-nfs-oods-auxtel-pvc',
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
    #     response['status'] = global_vars.STATUS_ERROR
    #     response['message'] = msg
    except Exception as e:
        msg = str(e)
        log.error(msg)
        response['message'] = msg
        response['status'] = global_vars.STATUS_ERROR
    return response
