import globals
import logging
import tornado.ioloop
import tornado.web
import tornado
import json
import os
from datetime import datetime, timedelta
import re
import base64

# Configure logging
log = logging.getLogger("uws_api_server")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
try:
    log.setLevel(os.environ['LOG_LEVEL'].upper())
except:
    log.setLevel('WARNING')

# Load Kubernetes API
try:
    import kubejob
except:
    log.warning('Failure loading Kubernetes client.')

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization")
        self.set_header("Access-Control-Allow-Methods",
                        " POST, PUT, DELETE, OPTIONS, GET")

    def options(self):
        self.set_status(204)
        self.finish()

    def getarg(self, arg, default=None):
        ''' 
        Calls to this function in BaseHandler.get(), BaseHandler.post(), etc must be surrounded by try/except blocks like so:
            
            try:
                ownerId = self.getarg('ownerId')
            except:
                self.finish()
                return
        
        '''
        value = default
        try:
            # If the request encodes arguments in JSON, parse the body accordingly
            if 'Content-Type' in self.request.headers and self.request.headers['Content-Type'] in ['application/json', 'application/javascript']:
                data = tornado.escape.json_decode(self.request.body)
                if default == None:
                    # The argument is required and thus this will raise an exception if absent
                    value = data[arg]
                else:
                    # Set the value to the default
                    value = default if arg not in data else data[arg]
            # Otherwise assume the arguments are in the default content type
            else:
                # The argument is required and thus this will raise an exception if absent
                if default == None:
                    value = self.get_argument(arg)
                else:
                    value = self.get_argument(arg, default)
        except Exception as e:
            response = str(e).strip()
            log.error(response)
            # 400 Bad Request: The server could not understand the request due to invalid syntax.
            # The assumption is that if a function uses `getarg()` to get a required parameter,
            # then the request must be a bad request if this exception occurs.
            self.send_response(response, http_status_code=globals.HTTP_BAD_REQUEST, return_json=False)
            raise e
        return value

    # The datetime type is not JSON serializable, so convert to string
    def json_converter(self, o):
        if isinstance(o, datetime):
            return o.__str__()
        
    def send_response(self, data, http_status_code=globals.HTTP_OK, return_json=True, indent=None):
        if return_json:
            if indent:
                self.write(json.dumps(data, indent=indent, default = self.json_converter))
            else:
                self.write(json.dumps(data, default = self.json_converter))
            self.set_header('Content-Type', 'application/json')
        else:
            self.write(data)
        self.set_status(http_status_code)


def valid_job_id(job_id):
    # For testing purposes, treat the string 'invalid_job_id' as an invalid job_id
    return isinstance(job_id, str) and len(job_id) > 0


def construct_job_object(job_info):
    job = {}
    try:
        creationTime = job_info['creation_time']
        startTime = job_info['status']['start_time']
        endTime = job_info['status']['completion_time']
        destructionTime = None # TODO: Should we track deletion time?
        try:
            executionDuration = (endTime - startTime).total_seconds()
        except:
            executionDuration = None
        try:
            message = job_info['message']
        except:
            message = ''
        # Determine job phase. For definitions see:
        #     https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#ExecutionPhase
        job_phase = 'unknown'
        if creationTime:
            job_phase = 'pending'
        if startTime:
            job_phase = 'queued'
            if job_info['status']['active']:
                job_phase = 'executing'
            if job_info['status']['failed']:
                job_phase = 'error'
        if endTime:
            job_phase = 'completed'
            if not job_info['status']['succeeded'] or job_info['status']['failed']:
                job_phase = 'error'
        
        results = []
        try:
            for filepath in job_info['output_files']:
                results.append({
                    'id': str(base64.b64encode(bytes(filepath, 'utf-8')), 'utf-8'),
                    'uri': filepath,
                    # 'mime-type': 'image/fits',
                    # 'size': '3000960',
                })
        except Exception as e:
            log.error(str(e))
            results = []
        # See job_schema.xml
        #   https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#jobobj
        job = {
            'jobId': job_info['job_id'],
            'runId': job_info['run_id'],
            'ownerId': '', # TODO: Track identity of job owner
            'phase': job_phase,
            'creationTime': creationTime,
            'startTime': startTime,
            'endTime': endTime,
            'executionDuration': executionDuration,
            'destruction': destructionTime,
            'parameters': {
                'command': job_info['command'],
                'environment': job_info['environment'],
            },
            'results': results,
            'errorSummary': {
                'message': message,
            },
            'jobInfo': {
            },
        }
    except Exception as e:
        log.error(str(e))
    return job


class JobHandler(BaseHandler):
    def put(self):
        try:
            # Command that the job container will execute
            command = self.getarg('command') # required 
            # Valid run_id value follows the Kubernetes label value constraints:
            #   - must be 63 characters or less (cannot be empty),
            #   - must begin and end with an alphanumeric character ([a-z0-9A-Z]),
            #   - could contain dashes (-), underscores (_), dots (.), and alphanumerics between.
            # See also:
            #   - https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#runId
            #   - https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
            run_id = self.getarg('run_id', default='') # optional
            if run_id and (run_id != re.sub(r'[^-._a-zA-Z0-9]', "", run_id) or not re.match(r'[a-zA-Z0-9]', run_id)):
                self.send_response('Invalid run_id. Must be 63 characters or less and begin with alphanumeric character and contain only dashes (-), underscores (_), dots (.), and alphanumerics between.', http_status_code=globals.HTTP_BAD_REQUEST, return_json=False)
                self.finish()
                return
            # The URL of the git repo to clone
            url = self.getarg('url', default='') # optional
            # The git reference (branch name or commit hash) to be checked out after cloning the git repo
            commit_ref = self.getarg('commit_ref', default='') # optional
            # environment is a list of environment variable names and values like [{'name': 'env1', 'value': 'val1'}]
            environment = self.getarg('environment', default=[]) # optional
            # Number of parallel job containers to run. The containers will execute identical code. Coordination is the 
            # responsibility of the job owner.
            replicas = self.getarg('replicas', default=1) # optional
        except:
            self.finish()
            return
        response = kubejob.create_job(
            command=command, 
            run_id=run_id,
            url=url, 
            commit_ref=commit_ref,
            replicas=replicas,
            environment=environment,
        )
        log.debug(response)
        if response['status'] != globals.STATUS_OK:
            self.send_response(response['message'], http_status_code=globals.HTTP_SERVER_ERROR, return_json=False)
            self.finish()
            return
        else:
            self.send_response(response, indent=2)
            self.finish()
            return
        
    def get(self, job_id=None, property=None):
        # See https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#resourceuri
        valid_properties = [
            'phase',
            # 'executionduration',
            # 'destruction',
            # 'error',
            # 'quote',
            'results',
            'parameters',
            # 'owner',
        ]
        response = {}
        # If no job_id is included in the request URL, return a list of jobs. See:
        # UWS Schema: https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#UWSSchema
        if not job_id:
            phase = self.getarg('phase', default='') # optional
            if not phase or phase in globals.VALID_JOB_STATUSES:
                results = kubejob.list_jobs()
                if results['status'] != globals.STATUS_OK:
                    self.send_response(results['message'], http_status_code=globals.HTTP_SERVER_ERROR, return_json=False)
                    self.finish()
                    return
            else:
                response = 'Valid job categories are: {}'.format(globals.VALID_JOB_STATUSES)
                self.send_response(response, http_status_code=globals.HTTP_BAD_REQUEST, return_json=False)
                self.finish()
                return
            # Construct the UWS-compatible list of job objects
            jobs = []
            for job_info in results['jobs']:
                job = construct_job_object(job_info)
                if not phase or job['phase'] == phase:
                    jobs.append(job)
            self.send_response(jobs, indent=2)
            self.finish()
            return
        # If a job_id is provided but it is invalid, then the request is malformed:
        if not valid_job_id(job_id):
            self.send_response('Invalid job ID.', http_status_code=globals.HTTP_BAD_REQUEST, indent=2)
            self.finish()
            return
        # If a property is provided but it is invalid, then the request is malformed:
        elif isinstance(property, str) and property not in valid_properties:
            self.send_response('Invalid job property requested.', http_status_code=globals.HTTP_BAD_REQUEST, indent=2)
            self.finish()
            return
        else:
            try:
                results = kubejob.list_jobs(
                    job_id=job_id, 
                )
                if results['status'] != globals.STATUS_OK:
                    self.send_response(results['message'], http_status_code=globals.HTTP_SERVER_ERROR, return_json=False)
                    self.finish()
                    return
                if not results['jobs']:
                    self.send_response(results['message'], http_status_code=globals.HTTP_NOT_FOUND)
                    self.finish()
                    return
                job = construct_job_object(results['jobs'][0])
                
                # If a specific job property was requested using an API endpoint 
                # of the form `/job/[job_id]/[property]]`, return that property only.
                # TODO: If the other API endpoints defined in the UWS pattern spec such 
                # as `executionduration` are implemented, there will need to be a mapping 
                # instead of direct key substitution, because `executionduration` corresponds
                # to `executionDuration` in the job object spec.
                if property in ['phase', 'results', 'parameters']:
                    self.send_response(job[property], indent=2)
                else:
                    self.send_response(job, indent=2)
                self.finish()
                return
            except Exception as e:
                response = str(e).strip()
                log.error(response)
                self.send_response(response, http_status_code=globals.HTTP_SERVER_ERROR, indent=2)
                self.finish()
                return

    def delete(self, job_id):
        response = kubejob.delete_job(
            job_id=job_id, 
        )
        log.debug(response)
        if response['status'] == globals.STATUS_ERROR:
            self.send_response(response['message'], http_status_code=globals.HTTP_SERVER_ERROR, return_json=False)
        elif isinstance(response['code'], int) and response['code'] != globals.HTTP_OK:
            self.send_response(response['message'], http_status_code=response['code'], return_json=False)
        else:
            self.send_response(response, indent=2)
        self.finish()
        return
        

def make_app(base_path=''):
    settings = {"debug": True}
    return tornado.web.Application(
        [
            # TODO: Move the job list handler into the /job endpoint to better implement the UWS pattern spec
            # See https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#jobList
            (r"{}/job/(.*)/(.*)".format(base_path), JobHandler),
            (r"{}/job/(.*)".format(base_path), JobHandler),
            (r"{}/job".format(base_path), JobHandler),
        ],
        **settings
    )


if __name__ == "__main__":
    app = make_app(base_path=globals.API_BASEPATH)
    app.listen(int(globals.API_PORT))
    log.info('UWS API server online at {}://{}:{}{}'.format(globals.API_PROTOCOL, globals.API_DOMAIN, globals.API_PORT, globals.API_BASEPATH))
    tornado.ioloop.IOLoop.current().start()
