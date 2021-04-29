UWS Client Demo
================================================

The following is a demonstration of basic job creation and management. The client is a Python script running the `client.py` script found here: https://github.com/lsst-dm/uws-api-server/blob/master/client/client.py.

The output of this script is the following:

```
Create a job:
PUT http://uws-api-server:80/api/v1/job :
HTTP code: 200
{
  "job_id": "acba01cb14bd48d585f5d0b3dc949cc8",
  "api_response": null,
  "message": null,
  "status": "ok"
}


List all jobs that are executing:
GET http://uws-api-server:80/api/v1/job?phase=executing :
HTTP code: 200
[
  {
    "jobId": "acba01cb14bd48d585f5d0b3dc949cc8",
    "runId": "hello-world",
    "ownerId": "",
    "phase": "executing",
    "creationTime": "2021-04-29 15:39:06+00:00",
    "startTime": "2021-04-29 15:39:06+00:00",
    "endTime": null,
    "executionDuration": null,
    "destruction": null,
    "parameters": {
      "command": [
        "/bin/bash",
        "-c",
        "cd $JOB_SOURCE_DIR && bash test/hello-world/hello-world.sh > $JOB_OUTPUT_DIR/hello-world.log\n"
      ],
      "environment": [
        {
          "name": "PROJECT_PATH",
          "value": "/project/manninga/projects"
        },
        {
          "name": "JOB_SOURCE_DIR",
          "value": "/uws/jobs/acba01cb14bd48d585f5d0b3dc949cc8/src"
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
          "value": "/uws/jobs/acba01cb14bd48d585f5d0b3dc949cc8/out"
        },
        {
          "name": "JOB_ID",
          "value": "acba01cb14bd48d585f5d0b3dc949cc8"
        },
        {
          "name": "PROJECT_SUBPATH",
          "value": "manninga/projects"
        },
        {
          "name": "CUSTOM_ENV_VAR",
          "value": "Success!"
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


Get the phase of the job just created:
GET /api/v1/job/acba01cb14bd48d585f5d0b3dc949cc8/phase :
HTTP code: 200
"executing"


Job acba01cb14bd48d585f5d0b3dc949cc8 phase is executing. Waiting to complete...
GET /api/v1/job/acba01cb14bd48d585f5d0b3dc949cc8/phase :
HTTP code: 200
"executing"


Job acba01cb14bd48d585f5d0b3dc949cc8 phase is executing. Waiting to complete...
GET /api/v1/job/acba01cb14bd48d585f5d0b3dc949cc8/phase :
HTTP code: 200
"completed"


Job phase is completed.
Fetching results...
GET /api/v1/job/acba01cb14bd48d585f5d0b3dc949cc8/results :
HTTP code: 200
[
  {
    "id": "L3V3cy9qb2JzL2FjYmEwMWNiMTRiZDQ4ZDU4NWY1ZDBiM2RjOTQ5Y2M4L291dC9oZWxsby13b3JsZC5sb2c=",
    "uri": "/uws/jobs/acba01cb14bd48d585f5d0b3dc949cc8/out/hello-world.log"
  }
]


Download result file to "./L3V3cy9qb2JzL2FjYmEwMWNiMTRiZDQ4ZDU4NWY1ZDBiM2RjOTQ5Y2M4L291dC9oZWxsby13b3JsZC5sb2c=".
Contents of result file "L3V3cy9qb2JzL2FjYmEwMWNiMTRiZDQ4ZDU4NWY1ZDBiM2RjOTQ5Y2M4L291dC9oZWxsby13b3JsZC5sb2c=":
Custom environment variable: Success!
Contents of project path "/project/manninga/projects" :
total 2
drwxr-xr-x 3 59214 202 4096 Apr 29 13:20 .
drwxr-xr-x 3     0   0   22 Apr 29 15:39 ..
drwxr-xr-x 3 59214 202 4096 Apr 29 13:20 test_gen3_discrete_skymap


```
