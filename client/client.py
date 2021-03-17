import globals
import requests
import json

# Import credentials and config from environment variables
config = {
    'apiBaseUrl': '{}://{}:{}{}'.format(globals.API_PROTOCOL, globals.API_DOMAIN, globals.API_PORT, globals.API_BASEPATH),
}


def list_jobs(category):
    response = requests.get(
        '{}/job/list/{}'.format(config['apiBaseUrl'], category),
    )
    try:
        print('GET {}/job/list/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, category, response.status_code, json.dumps(response.json(), indent=2)))
    except:
        print('GET {}/job/list/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, category, response.status_code, response))
    return response


def get_job(job_id, property=None):
    if property:
        response = requests.get(
            '{}/job/{}/{}'.format(config['apiBaseUrl'], job_id, property),
        )
        try:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, property, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{}/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, property, response.status_code, response))
    else:
        response = requests.get(
            '{}/job/{}'.format(config['apiBaseUrl'], job_id),
        )
        try:
            print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
        except:
            print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, response))
    return response


def create_job(command='sleep 120', url=None, commit_ref=None):
    payload = {
        'command': command,
        'url': url,
        'commit_ref': commit_ref,
    }
    response = requests.put(
        '{}/job'.format(config['apiBaseUrl']),
        json=payload
    )
    try:
        print('PUT {}/job :\npayload: {}\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, payload, response.status_code, json.dumps(response.json(), indent=2)))
        return response.json()
    except:
        print('PUT {}/job :\npayload: {}\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, payload, response.status_code, response))
        return response.text

def delete_job(job_id):
    response = requests.delete(
        '{}/job/{}'.format(config['apiBaseUrl'], job_id)
    )
    # print(response)
    try:
        print('DELETE {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
        return response.json()
    except:
        print('DELETE {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, response.text))
        return response.text


if __name__ == '__main__':

    # for category in ['all'] + globals.VALID_JOB_STATUSES + ['fake']:
    #     response = list_jobs(category)
    # for job_id in ['abcd123', 'invalid_job_id', '']:
    #     response = get_job(job_id)
    response = get_job('')
    response = get_job('fake')
    
    create_response = create_job()
    if not create_response['message']:
        list_response = get_job(create_response['job_id'])
    