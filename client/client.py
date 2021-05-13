from datetime import datetime
import requests
import json

# Load configuration file
try:
    with open('/etc/config/uws.yaml', "r") as conf_file:
        config = yaml.load(conf_file, Loader=yaml.FullLoader)
    config['apiBaseUrl'] = f'''{config['server']['protocol']}://{config['server']['service']}:{config['server']['port']}{config['server']['basePath']}'''
except Exception as e:
    log.error(str(e))


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
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, property, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(config['server']['basePath'], job_id, property, response.status_code, response))
    else:
        response = requests.get(
            '{}/job/{}'.format(config['apiBaseUrl'], job_id),
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
    visit = 903332
    detector = 19
    instrument = 'HSC'
    collection = 'shared/valid_hsc_all'
    creation_time = datetime.timestamp(datetime.now())
    out_collection = f'imgserv_{creation_time}'
    put_collection = f'imgserv_positions_{creation_time}'
    env_dict = {
        'PIPELINE_TASK_CLASS': 'lsst.pipe.tasks.calexpCutout.CalexpCutoutTask',
        'PROJECT_SUBPATH': 'krughoff/projects/uws_cutout',
        'BUTLER_REPO': '/project/krughoff/projects/uws_cutout/validation_hsc_gen3',
        'OUTPUT_COLLECTION': out_collection,
        'PUT_COLLECTION': put_collection,
        'RUN_OPTIONS': f'-i {collection},{put_collection}',
        'DATA_QUERY': f"visit={visit} AND detector={detector} AND instrument='{instrument}'",
        'OUTPUT_GLOB': 'calexp_cutouts',
        'CUTOUT_RA': 319.89828,
        'CUTOUT_DEC': -0.3882156,
        'CUTOUT_SIZE': 20,
        'VISIT': visit,
        'DETECTOR': detector,
        'INSTRUMENT': instrument,
        'JOB_IMAGE_TAG': '7-stack-lsst_distrib-w_2021_19',
    }
    environment = [{'name': k, 'value': v} for k, v in env_dict.items()]
    create_response = create_job(
        run_id='simons-cutout',
        command='cd $JOB_SOURCE_DIR && bash bin/simon_pipetask.sh i2>&1 > $JOB_OUTPUT_DIR/pipe_task.log',
        git_url='https://github.com/lsst-dm/uws_scripts',
        commit_ref='u/krughoff/DM-29375',
        environment=environment
    )
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
        print('Fetching results...')
        results = get_job(job_id, property='results').json()
        for result in results:
            downloaded_file = get_result(job_id=job_id, result_id=result['id'])
            if downloaded_file:
                print(f'Contents of result file "{downloaded_file}":')
                with open(downloaded_file, 'r') as dfile:
                    print(dfile.read())
