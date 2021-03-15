import globals
import logging
import tornado.ioloop
import tornado.web
import tornado
import json
import os
from datetime import datetime, timedelta



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
        
    def send_response(self, data, http_status_code=200, return_json=True, indent=None):
        if return_json:
            if indent:
                self.write(json.dumps(data, indent=indent, default = self.json_converter))
            else:
                self.write(json.dumps(data, default = self.json_converter))
            self.set_header('Content-Type', 'application/json')
        else:
            self.write(data)
        self.set_status(http_status_code)

class JobListHandler(BaseHandler):
    def get(self, category):
        # UWS Schema: https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#UWSSchema
        response = {
            'job_ids': [],
        }
        all_jobs = [
            'dummy_job_id_0_completed',
            'dummy_job_id_1_completed',
            'dummy_job_id_2_pending',
            'dummy_job_id_3_executing',
            'dummy_job_id_4',
            'dummy_job_id_5',
            'dummy_job_id_6',
        ]
        if category == 'all':
            response['job_ids'] = all_jobs
        elif category == 'completed':
            response['job_ids'] = all_jobs[0:2]
        elif category == 'pending':
            response['job_ids'] = [all_jobs[2]]
        elif category == 'executing':
            response['job_ids'] = [all_jobs[3]]
        elif category in globals.VALID_JOB_STATUSES:
            response['job_ids'] = [all_jobs[4]]
        else:
            response['message'] = 'Valid job categories are: {}'.format(globals.VALID_JOB_STATUSES)
            self.send_response(response, http_status_code=globals.HTTP_BAD_REQUEST)
            self.finish()
            return
        self.send_response(response, indent=2)
        self.finish()
        return

def valid_job_id(job_id):
    # For testing purposes, treat the string 'invalid_job_id' as an invalid job_id
    return isinstance(job_id, str) and len(job_id) > 0 and job_id != 'invalid_job_id'

class JobHandler(BaseHandler):
    def delete(self, job_id):
        response = kubejob.delete_job(
            job_id=job_id, 
        )
        log.debug(response)
        if response['status'] == globals.STATUS_ERROR:
            self.send_response(response, http_status_code=globals.HTTP_SERVER_ERROR)
        elif isinstance(response['code'], int) and response['code'] != 0:
            self.send_response(response, http_status_code=response['code'], indent=2)
        else:
            self.send_response(response, indent=2)
        self.finish()
        return
        
    def put(self):
        try:
            command = self.getarg('command') # required 
            # environment is a list of objects like [{'name': 'env1', 'value': 'val1'}]
            workdir = self.getarg('workdir', default='/scratch/uws') # optional
            environment = self.getarg('environment', default=[]) # optional
            replicas = self.getarg('replicas', default=1) # optional
        except:
            self.finish()
            return
        response = kubejob.create_job(
            command=command, 
            workdir=workdir, 
            replicas=replicas,
            environment=environment,
        )
        log.debug(response)
        self.send_response(response, indent=2)
        self.finish()
        return
        
    def get(self, job_id):
        response = {}
        log.debug(f'Get job_id = {job_id}')
        # <job> object: https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#jobobj
        # If no job_id is provided, then the request is malformed:
        if isinstance(job_id, str) and len(job_id) == 0:
            self.send_response(response, http_status_code=globals.HTTP_BAD_REQUEST, indent=2)
            self.finish()
            return
        # If the job_id is provided but is 
        elif not valid_job_id(job_id):
            self.send_response(response, http_status_code=globals.HTTP_BAD_REQUEST, indent=2)
            self.finish()
            return
        else:
            try:
                response = kubejob.list_job(
                    job_id=job_id, 
                )
                # log.debug(response)
                if response:
                    self.send_response(response, indent=2)
                else:
                    self.send_response(response, http_status_code=globals.HTTP_NOT_FOUND)
                self.finish()
                return
            except Exception as e:
                response = str(e).strip()
                log.error(response)
                self.send_response(response, http_status_code=globals.HTTP_SERVER_ERROR, indent=2)
                self.finish()
                return
                
            endTime = datetime.utcnow()
            startTime = endTime - timedelta(hours=1.0)
            executionDuration = endTime - startTime,
            creationTime = startTime - timedelta(hours=1.0)
            destructionTime = endTime + timedelta(hours=1.0)
            # See job_schema.xml
            #   https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#jobobj
            response = {
                'jobId': job_id,
                'runId': 'run-{}'.format(job_id),
                'ownerId': 'jsmith',
                'creationTime': creationTime,
                'startTime': startTime,
                'endTime': endTime,
                'executionDuration': (endTime - startTime).total_seconds(),
                'destruction': destructionTime,
                'parameters': {
                    'first': 1.0,
                    'second': 'two',
                },
                'results': {
                    'meets_criteria': False,
                },
                'errorSummary': '',
                'jobInfo': {
                    'anything': 'that',
                    'you': 'want',
                },
            }
            log.debug(json.dumps(response, indent=2, default = self.json_converter))
            self.send_response(response, indent=2)
            self.finish()
            return


def make_app(base_path=''):
    settings = {"debug": True}
    return tornado.web.Application(
        [
            (r"{}/job/list/(.*)".format(base_path), JobListHandler),
            (r"{}/job".format(base_path), JobHandler),
            (r"{}/job/(.*)".format(base_path), JobHandler),
        ],
        **settings
    )


if __name__ == "__main__":
    app = make_app(base_path=globals.API_BASEPATH)
    app.listen(int(globals.API_PORT))
    log.info('UWS API server online at {}://{}:{}{}'.format(globals.API_PROTOCOL, globals.API_DOMAIN, globals.API_PORT, globals.API_BASEPATH))
    tornado.ioloop.IOLoop.current().start()
