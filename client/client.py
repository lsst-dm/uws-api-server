import global_vars
import requests
import json

# Import credentials and config from environment variables
config = {
    'apiBaseUrl': '{}://{}:{}{}'.format(global_vars.API_PROTOCOL, global_vars.API_DOMAIN, global_vars.API_PORT, global_vars.API_BASEPATH),
}


def get_result(job_id=None, result_id=''):
    url = f'{config["apiBaseUrl"]}/job/result/{job_id}/{result_id}'
    try:
        local_filename = url.split('/')[-1]
        # NOTE the stream=True parameter below
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk: 
                    f.write(chunk)
        print(f'Download result file to "./{local_filename}".')
        return local_filename
    except Exception as e:
        print(f'Error fetching result file: {str(e)}')
        return None


def list_jobs(phase=''):
    phaseQuery = f'?phase={phase}' if phase else ''
    url = f'{config["apiBaseUrl"]}/job{phaseQuery}'
    response = requests.get(url)
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
        )
        try:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(global_vars.API_BASEPATH, job_id, property, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(global_vars.API_BASEPATH, job_id, property, response.status_code, response))
    else:
        response = requests.get(
            '{}/job/{}'.format(config['apiBaseUrl'], job_id),
        )
        try:
            print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(global_vars.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(global_vars.API_BASEPATH, job_id, response.status_code, response))
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
        json=payload
    )
    try:
        responseText = json.dumps(response.json(), indent=2)
    except:
        responseText = json.dumps(response.text)
    print(f'PUT {url} :\nHTTP code: {response.status_code}\n{responseText}\n\n')
    return response

def delete_job(job_id):
    response = requests.delete(
        '{}/job/{}'.format(config['apiBaseUrl'], job_id)
    )
    # print(response)
    try:
        print('DELETE {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(global_vars.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
        return response.json()
    except:
        print('DELETE {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(global_vars.API_BASEPATH, job_id, response.status_code, response.text))
        return response.text


if __name__ == '__main__':
    import time
    
    # # DELETE ALL JOBS AND JOB FILES:
    # for job in list_jobs().json():
    #     print(f'Deleting job {job["jobId"]}...')
    #     delete_job(job['jobId'])
    
    print('List all jobs:')
    list_jobs()
    
    print('Create a job:')
    # create_response = create_job(command='ls -l > $JOB_OUTPUT_DIR/dirlist.txt', git_url='https://github.com/lsst-dm/uws-api-server', run_id='my-special-job')
    create_response = create_job(
        run_id='andrew',
        command='cd $JOB_SOURCE_DIR && mkdir $JOB_OUTPUT_DIR/subdir1 && mkdir $JOB_OUTPUT_DIR/subdir2 && bash test/hello-world/hello-world.sh | tee $JOB_OUTPUT_DIR/hello-world.log | tee $JOB_OUTPUT_DIR/subdir1/hello-world.log | tee $JOB_OUTPUT_DIR/subdir2/hello-world.log', 
        git_url='https://github.com/lsst-dm/uws-api-server',
        environment=[
            {
                'name': 'PROJECT_SUBPATH',
                'value': 'manninga/projects',
            },
            {
                'name': 'CUSTOM_ENV_VAR',
                'value': 'Success!',
            },
        ]
    )
    job_id = create_response.json()['job_id']
    
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
        print('Fetching results...')
        results = get_job(job_id, property='results').json()
        for result in results:
            downloaded_file = get_result(job_id=job_id, result_id=result['id'])
            if downloaded_file:
                print(f'Contents of result file "{downloaded_file}":')
                with open(downloaded_file, 'r') as dfile:
                    print(dfile.read())
