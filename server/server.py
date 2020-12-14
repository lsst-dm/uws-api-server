from globals import STATUS_OK, STATUS_ERROR, VALID_JOB_STATUSES
import envvars
import logging
import tornado.ioloop
import tornado.web
from tornado.gen import coroutine
import tornado
import json
import os
from datetime import datetime, timedelta

# Configure logging
log_format = "%(asctime)s  %(name)8s  %(levelname)5s  %(message)s"
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("test.log"), logging.StreamHandler()],
    format=log_format,
)
logger = logging.getLogger("server")

# The datetime type is not JSON serializable, so convert to string
def json_converter(o):
    if isinstance(o, datetime):
        return o.__str__()

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
        response = {
            'status': STATUS_OK,
            'message': ''
        }
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
            response['status'] = STATUS_ERROR
            response['message'] = str(e).strip()
            logger.error(response['message'])
            # 400 Bad Request: The server could not understand the request due to invalid syntax.
            # The assumption is that if a function uses `getarg()` to get a required parameter,
            # then the request must be a bad request if this exception occurs.
            self.set_status(400)
            self.write(json.dumps(response))
            self.finish()
            raise e
        return value


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
        elif category in VALID_JOB_STATUSES:
            response['job_ids'] = [all_jobs[4]]
        else:
            response['message'] = 'Valid job categories are: {}'.format(VALID_JOB_STATUSES)
            self.set_status(400)
            self.write(response)
            self.finish()
            return
        self.write(response)

def valid_job_id(job_id):
    # For testing purposes, treat the string 'invalid_job_id' as an invalid job_id
    return isinstance(job_id, str) and len(job_id) > 0 and job_id != 'invalid_job_id'

class JobHandler(BaseHandler):
    def get(self, job_id):
        response = {}
        # <job> object: https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#jobobj
        # If no job_id is provided, then the request is malformed:
        if isinstance(job_id, str) and len(job_id) == 0:
            self.set_status(400)
            self.write(json.dumps(response, indent=4, default = json_converter))
            self.finish()
        # If the job_id is provided but is 
        elif not valid_job_id(job_id):
            self.set_status(404)
            self.write(json.dumps(response, indent=4, default = json_converter))
            self.finish()
        else:
            endTime = datetime.utcnow()
            startTime = endTime - timedelta(hours=1.0)
            creationTime = startTime - timedelta(hours=1.0)
            response = {
                'jobId': job_id,
                'runId': 'run-{}'.format(job_id),
                'ownerId': 'jsmith',
                'creationTime': creationTime,
                'startTime': startTime,
                'endTime': endTime,
                'executionDuration': endTime - startTime,
                'jobInfo': {
                    'anything': 'that',
                    'you': 'want',
                },
                'results': {},
                'parameters': {
                    'first': 1.0,
                    'second': 'two',
                },
                'errorSummary': '',
            }
            self.write(json.dumps(response, indent=4, default = json_converter))


def make_app(base_path=''):
    settings = {"debug": True}
    return tornado.web.Application(
        [
            (r"{}/job/list/(.*)".format(base_path), JobListHandler),
            (r"{}/job/(.*)".format(base_path), JobHandler),
        ],
        **settings
    )


if __name__ == "__main__":
    app = make_app(base_path=envvars.API_BASEPATH)
    app.listen(envvars.API_PORT)
    logger.info('Running at {}:{}{}'.format(envvars.API_DOMAIN, envvars.API_PORT, envvars.API_BASEPATH))
    tornado.ioloop.IOLoop.current().start()
