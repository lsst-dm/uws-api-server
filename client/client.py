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


def get_job(job_id):
    response = requests.get(
        '{}/job/{}'.format(config['apiBaseUrl'], job_id),
    )
    try:
        print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
    except:
        print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, response))
    return response


def create_job():
    payload = {
            'command': 'sleep 600',
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


def list_job(job_id):
    response = requests.get(
        '{}/job/{}'.format(config['apiBaseUrl'], job_id)
    )
    # print(response)
    try:
        print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, json.dumps(response.json(), indent=2)))
        return response.json()
    except:
        print('GET {}/job/{} :\nHTTP code: {}\n{}\n\n'.format(globals.API_BASEPATH, job_id, response.status_code, response.text))
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
    response = list_job('')
    response = list_job('fake')
    
    create_response = create_job()
    if not create_response['message']:
        list_response = list_job(create_response['job_id'])
    
    delete_response = delete_job('e13d8336c2e940ff8efb0d7f80cba384')
    delete_response = delete_job('9072b44fb46d4a3aa57d513b28b72c3f')
    delete_response = delete_job('b4c5336a0acf47e699bd0bb7a90f5d08')
    delete_response = delete_job('8662576fbec64f5ca2f53ccaab8aafb0')