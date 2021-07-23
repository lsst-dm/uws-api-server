from datetime import datetime
import requests
import json
import os
import sys
from base64 import b64encode

## Set an environment variable UWS_USER_PASS with the basic auth credentials prior to running this script:
#
#      export UWS_USER_PASS='user:pass'
#      python3 client.local.py
#
#
config = {
    'server': {
        'basePath': '/api/v1',
    },
    'apiBaseUrl': 'https://lsst-nts-k8s.ncsa.illinois.edu/uws-server/api/v1',
    # 'apiBaseUrl': 'https://summit-lsp.lsst.codes/uws-server/api/v1',
    'auth': b64encode(bytes(f"{os.environ['UWS_USER_PASS']}", 'utf-8')).decode("ascii"),
}
auth_header = {'Authorization': f'Basic {config["auth"]}'}

def get_result(job_id=None, result=None):
    url = f'{config["apiBaseUrl"]}/job/result/{job_id}/{result["id"]}'
    try:
        # local_filename = os.path.basename(result['uri'])
        # local_dir = os.path.join('.', os.path.dirname(result['uri']))
        # local_filepath = os.path.join(local_dir, local_filename)
        local_filepath = os.path.join(os.path.abspath(os.getcwd()), result['uri'].strip('/') )
        print(f'Downloading result {result["id"]} to "{local_filepath}"...')
        # NOTE the stream=True parameter below
        with requests.get(
            url, 
            stream=True,
            headers=auth_header,
        ) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(local_filepath), exist_ok=True)
            with open(local_filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk: 
                    f.write(chunk)
        print(f'    Download complete.')
        return local_filepath
    except Exception as e:
        print(f'Error fetching result file: {str(e)}')
        return None


def list_jobs(phase=''):
    phaseQuery = f'?phase={phase}' if phase else ''
    url = f'{config["apiBaseUrl"]}/job{phaseQuery}'
    response = requests.get(
        url,
        headers=auth_header,
    )
    try:
        responseText = json.dumps(response.json(), indent=2)
    except:
        responseText = json.dumps(response.text)
    print(f'GET {url} :\nHTTP code: {response.status_code}\n{responseText}\n\n')
    return response


def get_job(job_id, property=None):
    if property:
        response = requests.get(
            '{}/job/{}/{}'.format(config['apiBaseUrl'], job_id, property),
            headers=auth_header,
        )
        try:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, property, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, property, response.status_code, response))
    else:
        response = requests.get(
            '{}/job/{}'.format(config['apiBaseUrl'], job_id),
            headers=auth_header,
        )
        try:
            print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, response.status_code, response))
    return response


def create_job(command='sleep 120', run_id=None, environment=[], git_url=None, commit_ref=None):
    payload = {
        'command': command,
        'run_id': run_id,
        'environment': environment,
        'url': git_url,
        'commit_ref': commit_ref,
    }
    url = f'{config["apiBaseUrl"]}/job'
    response = requests.put(
        url=url,
        json=payload,
        headers=auth_header,
    )
    try:
        responseText = json.dumps(response.json(), indent=2)
    except:
        responseText = response.text
    print(f'PUT {url} :\nHTTP code: {response.status_code}\n{responseText}\n\n')
    return response

def delete_job(job_id):
    response = requests.delete(
        '{}/job/{}'.format(config['apiBaseUrl'], job_id),
        headers=auth_header,
    )
    # print(response)
    try:
        print('DELETE {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, response.status_code, json.dumps(response.json(), indent=2)))
        return response.json()
    except:
        print('DELETE {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, response.status_code, response.text))
        return response.text


if __name__ == '__main__':
    import time
    from datetime import datetime
    
    # # DELETE ALL JOBS AND JOB FILES:
    # for job in list_jobs().json():
    #     # if job['runId'] == '12345678':
    #         print(f'Deleting job {job["jobId"]}...')
    #         delete_job(job['jobId'])
    
    # print('List all jobs:')
    # list_jobs()
    # import sys
    # sys.exit(0)

    print('Create a job:')
    # payload_env = dict(
    #     EUPS_TAG="",
    #     PIPELINE_URL='$OBS_LSST_DIR/pipelines/DRP.yaml#isr',
    #     BUTLER_REPO='/repo/LATISS',
    #     RUN_OPTIONS="-c isr:doBias=False -c isr:doDark=False -c isr:doFlat=False -c isr:doFringe=False -c isr:doLinearize=False -c isr:doDefect=False -i LATISS/raw/all",
    #     DATA_QUERY="instrument='LATISS' AND exposure.day_obs=20210414 AND exposure.seq_num=2",
    #     OUTPUT_GLOB='*',
    # )
    # create_response = create_job(
    #     run_id='pipetask',
    #     command='cd $JOB_SOURCE_DIR && bash bin/pipetask.sh',
    #     # command='sleep 10m',
    #     git_url='https://github.com/lsst-dm/uws_scripts',
    #     commit_ref='17b49f053bcdacf53f420db251e36503e56e0293',
    #     environment=[dict(name=k, value=v) for k, v in payload_env.items()],
    # )
    
    payload_env = dict(
        CUSTOM_ENV_VAR="Hello OCPS!",
    )
    create_response = create_job(
        run_id='hello-world',
        command='cd $JOB_SOURCE_DIR && bash test/hello-world/hello-world.sh',
        git_url='https://github.com/lsst-dm/uws-api-server',
        commit_ref='d044eee155f1019c4da737271653a21d9907601c',
        environment=[dict(name=k, value=v) for k, v in payload_env.items()],
    )
    
    if create_response.status_code != 200:
        print("ERROR. Aborting.")
        sys.exit(1)
    else:
        job_id = create_response.json()['jobId']
    
    print('List jobs that are executing:')
    list_jobs(phase='executing')
    
    print('Get the phase of the job just created:')
    job_phase = get_job(job_id, property='phase').json()
    while job_phase in ['pending', 'queued', 'executing']:
        print(f'Job {job_id} phase is {job_phase}. Waiting to complete...')
        time.sleep(3)
        job_phase = get_job(job_id, property='phase').json()
    print(f'Job phase is {job_phase}.')
    
    # Show output files
    if job_phase == 'completed':
        wait_sec = 0
        print(f'Fetching results (wait {wait_sec} seconds)...')
        time.sleep(wait_sec)
        results = get_job(job_id, property='results').json()
        for result in results:
            downloaded_file = get_result(job_id=job_id, result=result)
            # if downloaded_file:
            #     print(f'Contents of result file "{downloaded_file}":')
            #     with open(downloaded_file, 'r') as dfile:
            #         print(dfile.read())
