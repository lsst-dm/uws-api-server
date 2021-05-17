
const apispecyaml = `
################################################################################
openapi: 3.0.1
info:
  title: OCS Universal Worker Service API
  description: "Rubin OCS Universal Worker Service API"
  version: 1.0.0
servers:
- url: /api/v1/
  description: API endpoint base path
tags:
- name: Jobs
  description: Manage jobs
- name: Results
  description: Manage results
paths:
  /job:
    get:
      tags:
      - Jobs
      summary: Fetch a list of jobs
      operationId: listJobs
      parameters:
      - in: query
        name: phase
        required: false
        description: >
            List jobs in a specific phase.
        schema:
          $ref: '#/components/schemas/ListJobPhases'
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ListJobResponse"
        "400":
          description: Invalid category supplied
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
    put:
      tags:
      - Jobs
      summary: Submit a new job
      description: ""
      operationId: newJob
      requestBody:
        description: |
          Job specification
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/PutJob"
        required: true
      responses:
        "200":
          description: Job submission status and ID
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GetJob"
        "400":
          description: Invalid syntax
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  "/job/{job_id}":
    get:
      tags:
      - Jobs
      summary: Fetch the details of a specific job
      operationId: getJob
      parameters:
      - name: job_id
        in: path
        description: ID of job to return
        required: true
        schema:
          type: string
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GetJob"
        "400":
          description: Invalid ID supplied
        "404":
          description: Job not found
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
    delete:
      tags:
      - Jobs
      summary: Delete a job
      description: ""
      operationId: deleteJob
      parameters:
      - name: job_id
        in: path
        description: ID of job to delete
        required: true
        schema:
          type: string
      responses:
        "200":
          description: successful operation
        "400":
          description: Invalid ID supplied
        "404":
          description: Job not found
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  "/job/{job_id}/{property}":
    get:
      tags:
      - Jobs
      summary: Fetch specific property of an existing job
      operationId: getJobProperty
      parameters:
      - name: job_id
        in: path
        description: ID of job to return
        required: true
        schema:
          type: string
      - name: property
        in: path
        required: true
        description: Fetch a specific property of a job
        schema:
          $ref: '#/components/schemas/JobProperty'
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/JobPropertyValue"
        "400":
          description: Invalid ID or property supplied
        "404":
          description: Job not found
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  "/job/result/{job_id}/{result_id}":
    get:
      tags:
      - Results
      summary: Download an output file of an existing job
      operationId: getJobResult
      parameters:
      - name: job_id
        in: path
        description: ID of job that generated the desired file
        required: true
        schema:
          type: string
      - name: result_id
        in: path
        required: true
        description: ID of result/output file
        schema:
          type: integer
      responses:
        "200":
          description: successful operation
          content:
            '*/*':
              schema: 
                type: string
                format: binary
        "400":
          description: Invalid job ID or result ID supplied
        "404":
          description: File not found
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
components:
  schemas:
    GenericServerError:
      type: object
      properties:
        message:
          type: string
          description: Explanation of error
          example: "Error due to XYZ"
    GetJob:
      type: object
      properties:
        jobId:
          type: string
          description: Job ID
          example: "51871bb0015c4b49bf5dcf4011d99975"
        runId:
          type: string
          description: Optional non-unique label attached to job
          example: "astro-job"
        phase:
          type: string
          description: Job phase
          example: "executing"
        creationTime:
          type: string
          description: Job creation time
          example: "2021-04-29 15:39:06+00:00"
        startTime:
          type: string
          description: Job execution start time
          example: "2021-04-29 15:39:09+00:00"
        endTime:
          type: string
          description: Job completion time
          example: "2021-04-29 15:41:06+00:00"
        destruction:
          type: string
          description: Job destruction time (not implemented)
          example: "2021-04-29 15:41:06+00:00"
        executionDuration:
          type: integer
          description: Job duration in seconds
          example: "543"
        parameters:
          $ref: '#/components/schemas/JobParameters'
        results:
          $ref: '#/components/schemas/JobResults'
    JobParameters:
      type: object
      description: Input parameter values.
      properties:
        command:
          type: array
          description: Command to execute 
          items:
            type: string
            example: 
            - /bin/sh
            - -c
            - sleep 1d
        environment:
          $ref: '#/components/schemas/JobEnvironment'
    JobResults:
      type: array
      description: Job output files
      items:
        type: object
        properties:
          id:
            type: integer
            description: Result ID associated with one output file
            example: 0
          path:
            type: string
            description: Relative path of an output file
            example: /uws/jobs/3151ec18cace4bf0946b95e958c0edc6/out/my_file.dat
    JobProperty:
      type: string
      description: Job property to fetch
      enum:
      - 'results'
      - 'phase'
      - 'parameters'
    JobPropertyValue:
      oneOf:
      - $ref: "#/components/schemas/ListJobPhases"
      - $ref: "#/components/schemas/JobResults"
      - $ref: "#/components/schemas/JobParameters"
    ListJobPhases:
      type: string
      enum:
      - 'pending'
      - 'queued'
      - 'executing'
      - 'completed'
      - 'error'
      - 'unknown'
      - 'held'
      - 'suspended'
      - 'aborted'
    ListJobResponse:
      type: array
      items:
        $ref: '#/components/schemas/GetJob'
    PutJob:
      type: object
      properties:
        run_id:
          type: string
          description: Optional label for job. Does not need to be unique.
          example: "astro-job"
        command:
          type: string
          description: Command to execute in the bash shell
          example: "sleep 30"
        url:
          type: string
          description: Git repo URL to clone for source code
          example: "https://gitlab.com/lsst-dm/example-repo"
        commit_ref:
          type: string
          description: Git repo ref (e.g. branch name, tag, commit hash)
          example: "78494ed"
        environment:
          $ref: '#/components/schemas/JobEnvironment'
        replicas:
          type: integer
          description: Optional number of parallel containers to spawn
          example: 1
    JobEnvironment:
      type: array
      description: Environment variables and values
      items:
        type: object
        properties:
          name:
            type: string
            description: Name of environment variable
            example: "PROJECT_PATH"
          value:
            type: string
            description: Value of environment variable
            example: "username/projects"
################################################################################
`;
