from globals import STATUS_OK, STATUS_ERROR, VALID_JOB_STATUSES
import envvars
import requests
import json

# Import credentials and config from environment variables
config = {
    'apiBaseUrl': '{}://{}:{}{}'.format(envvars.API_PROTOCOL, envvars.API_DOMAIN, envvars.API_PORT, envvars.API_BASEPATH),
}


def list_jobs(category):
    response = requests.get(
        '{}/job/list/{}'.format(config['apiBaseUrl'], category),
    )
    try:
        print('GET {}/job/list/{} :\nHTTP code: {}\n{}\n\n'.format(envvars.API_BASEPATH, category, response.status_code, json.dumps(response.json(), indent=2)))
    except:
        print('GET {}/job/list/{} :\nHTTP code: {}\n{}\n\n'.format(envvars.API_BASEPATH, category, response.status_code, response))
    return response


def get_job(job_id):
    response = requests.get(
        '{}/job/{}'.format(config['apiBaseUrl'], job_id),
    )
    try:
        print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(envvars.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
    except:
        print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(envvars.API_BASEPATH, job_id, response.status_code, response))
    return response


def create_job():
    response = requests.put(
        '{}/job'.format(config['apiBaseUrl']),
    )
    print(response)
    try:
        print('PUT {}/job :\nHTTP code: {}\n{}\n\n'.format(envvars.API_BASEPATH, response.status_code, json.dumps(response.json(), indent=2)))
    except:
        print('PUT {}/job :\nHTTP code: {}\n{}\n\n'.format(envvars.API_BASEPATH, response.status_code, response))
    return response


if __name__ == '__main__':

    for category in ['all'] + VALID_JOB_STATUSES + ['fake']:
        response = list_jobs(category)
    for job_id in ['abcd123', 'invalid_job_id', '']:
        response = get_job(job_id)
    response = create_job()