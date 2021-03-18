UWS Client Demo
================================================

The following is a demonstration of basic job creation and management. The client is a Python script running the following code:

```
print('List all jobs:')
list_jobs()
print('Create a job:')
create_response = create_job(command='ls -l > $JOB_OUTPUT_DIR/dirlist.txt', git_url='https://github.com/lsst-dm/uws-api-server', run_id='my-special-job')
job_id = create_response.json()['job_id']
print('List jobs that are executing:')
list_jobs(phase='executing')
print('Get the results for the job just created:')
job_phase = get_job(job_id, property='phase').json()
while job_phase in ['pending', 'queued', 'executing']:
    print(f'Job {job_id} phase is {job_phase}. Waiting to complete...')
    time.sleep(3)
    job_phase = get_job(job_id, property='phase').json()
print(f'Job phase is {job_phase}.')
if job_phase == 'completed':
    print('Fetching results...')
    results = get_job(job_id, property='results').json()
    for result in results:
        downloaded_file = get_result(result_id=result['id'])
        if downloaded_file:
            print(f'Contents of result file "{downloaded_file}":')
            with open(downloaded_file, 'r') as dfile:
                print(dfile.read())
```

The output of this script is the following:

```
worker@uws-api-client-67dd546754-xqbdn:~/client$ python3 client.py 

List all jobs:
GET http://uws-api-server:80/api/v1/job :
HTTP code: 200
[
  {
    "jobId": "a6b9043ef0c24170b019641da57a0dba",
    "runId": "my-special-job",
    "ownerId": "",
    "phase": "completed",
    "creationTime": "2021-03-17 20:58:00+00:00",
    "startTime": "2021-03-17 20:58:00+00:00",
    "endTime": "2021-03-17 20:58:13+00:00",
    "executionDuration": 13.0,
    "destruction": null,
    "parameters": {
      "command": [
        "/bin/bash",
        "-c",
        "cd /uws/jobs/a6b9043ef0c24170b019641da57a0dba/src && ls -l > $JOB_OUTPUT_DIR/dirlist.txt"
      ],
      "environment": [
        {
          "name": "DATA_DIR_COMCAM",
          "value": "/data/lsstdata/comcam/oods/gen3butler/repo"
        },
        {
          "name": "DATA_DIR_AUXTEL",
          "value": "/data/lsstdata/auxTel/oods/gen3butler/repo"
        },
        {
          "name": "JOB_SOURCE_DIR",
          "value": "/uws/jobs/a6b9043ef0c24170b019641da57a0dba/src"
        },
        {
          "name": "SRC_GIT_URL",
          "value": "https://github.com/lsst-dm/uws-api-server"
        },
        {
          "name": "GIT_COMMIT_REF",
          "value": null
        },
        {
          "name": "JOB_OUTPUT_DIR",
          "value": "/uws/jobs/a6b9043ef0c24170b019641da57a0dba/out"
        }
      ]
    },
    "results": [
      {
        "id": "L3V3cy9qb2JzL2E2YjkwNDNlZjBjMjQxNzBiMDE5NjQxZGE1N2EwZGJhL291dC9kaXJsaXN0LnR4dA==",
        "uri": "/uws/jobs/a6b9043ef0c24170b019641da57a0dba/out/dirlist.txt"
      }
    ],
    "errorSummary": {
      "message": ""
    },
    "jobInfo": {}
  }
]


Create a job:
PUT http://uws-api-server:80/api/v1/job :
HTTP code: 200
{
  "job_id": "e13ed9f2803842409763b185d4f490e2",
  "api_response": null,
  "message": null,
  "status": "ok"
}


List jobs that are executing:
GET http://uws-api-server:80/api/v1/job?phase=executing :
HTTP code: 200
[
  {
    "jobId": "e13ed9f2803842409763b185d4f490e2",
    "runId": "my-special-job",
    "ownerId": "",
    "phase": "executing",
    "creationTime": "2021-03-17 20:58:54+00:00",
    "startTime": "2021-03-17 20:58:54+00:00",
    "endTime": null,
    "executionDuration": null,
    "destruction": null,
    "parameters": {
      "command": [
        "/bin/bash",
        "-c",
        "cd /uws/jobs/e13ed9f2803842409763b185d4f490e2/src && ls -l > $JOB_OUTPUT_DIR/dirlist.txt"
      ],
      "environment": [
        {
          "name": "DATA_DIR_COMCAM",
          "value": "/data/lsstdata/comcam/oods/butler/repo"
        },
        {
          "name": "DATA_DIR_AUXTEL",
          "value": "/data/lsstdata/auxTel/oods/butler/repo"
        },
        {
          "name": "JOB_SOURCE_DIR",
          "value": "/uws/jobs/e13ed9f2803842409763b185d4f490e2/src"
        },
        {
          "name": "SRC_GIT_URL",
          "value": "https://github.com/lsst-dm/uws-api-server"
        },
        {
          "name": "GIT_COMMIT_REF",
          "value": null
        },
        {
          "name": "JOB_OUTPUT_DIR",
          "value": "/uws/jobs/e13ed9f2803842409763b185d4f490e2/out"
        }
      ]
    },
    "results": [],
    "errorSummary": {
      "message": ""
    },
    "jobInfo": {}
  }
]


Get the results for the job just created:
GET /api/v1/job/e13ed9f2803842409763b185d4f490e2/phase :
HTTP code: 200
"executing"

...


Job e13ed9f2803842409763b185d4f490e2 phase is executing. Waiting to complete...
GET /api/v1/job/e13ed9f2803842409763b185d4f490e2/phase :
HTTP code: 200
"executing"


Job e13ed9f2803842409763b185d4f490e2 phase is executing. Waiting to complete...
GET /api/v1/job/e13ed9f2803842409763b185d4f490e2/phase :
HTTP code: 200
"completed"


Job phase is completed.
Fetching results...
GET /api/v1/job/e13ed9f2803842409763b185d4f490e2/results :
HTTP code: 200
[
  {
    "id": "L3V3cy9qb2JzL2UxM2VkOWYyODAzODQyNDA5NzYzYjE4NWQ0ZjQ5MGUyL291dC9kaXJsaXN0LnR4dA==",
    "uri": "/uws/jobs/e13ed9f2803842409763b185d4f490e2/out/dirlist.txt"
  }
]


Download result file to "./L3V3cy9qb2JzL2UxM2VkOWYyODAzODQyNDA5NzYzYjE4NWQ0ZjQ5MGUyL291dC9kaXJsaXN0LnR4dA==".
Contents of result file "L3V3cy9qb2JzL2UxM2VkOWYyODAzODQyNDA5NzYzYjE4NWQ0ZjQ5MGUyL291dC9kaXJsaXN0LnR4dA==":
total 36
-rw-r--r-- 1 lsst lsst  653 Mar 17 20:59 Dockerfile
-rw-r--r-- 1 lsst lsst  436 Mar 17 20:59 Readme.rst
drwxr-xr-x 2 lsst lsst   98 Mar 17 20:59 client
drwxr-xr-x 4 lsst lsst  273 Mar 17 20:59 docs
-rw-r--r-- 1 lsst lsst  399 Mar 17 20:59 envvars.py
-rw-r--r-- 1 lsst lsst 1186 Mar 17 20:59 globals.py
-rwxr-xr-x 1 lsst lsst 1096 Mar 17 20:59 k8s_sync_client.sh
-rwxr-xr-x 1 lsst lsst 1096 Mar 17 20:59 k8s_sync_server.sh
-rwxr-xr-x 1 lsst lsst  383 Mar 17 20:59 launch_job_manager.sh
-rw-r--r-- 1 lsst lsst  142 Mar 17 20:59 requirements.txt
-rwxr-xr-x 1 lsst lsst  449 Mar 17 20:59 run_client.sh
drwxr-xr-x 3 lsst lsst  212 Mar 17 20:59 server

```