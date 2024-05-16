import json
import logging
import os
import re
import time
from datetime import datetime
from mimetypes import guess_type

import global_vars
import tornado
import tornado.ioloop
import tornado.web
from global_vars import config

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s",
)
log = logging.getLogger("uws-server")
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s [%(name)-12s]
# %(levelname)-8s %(message)s')
# handler.setFormatter(formatter)
# log.addHandler(handler)
try:
    log.setLevel(config["server"]["logLevel"].upper())
except KeyError:
    log.setLevel("WARNING")

# Load Kubernetes API
try:
    import kubejob
except ImportError:
    log.warning("Failure loading Kubernetes client.")


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header(
            "Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization"
        )
        self.set_header("Access-Control-Allow-Methods", " POST, PUT, DELETE, OPTIONS, GET")

    def options(self):
        self.set_status(204)
        self.finish()

    def getarg(self, arg, default=None):
        """
        Get argument from JSON body.

        Calls this function in BaseHandler.get(), BaseHandler.post(), etc
        must be surrounded by try/except blocks like so:

            try:
                ownerId = self.getarg('ownerId')
            except Exception:
                self.finish()
                return

        """
        value = default
        try:
            # If the request encodes arguments in JSON, parse the body
            # accordingly
            if "Content-Type" in self.request.headers and self.request.headers["Content-Type"] in [
                "application/json",
                "application/javascript",
            ]:
                data = tornado.escape.json_decode(self.request.body)
                if default is None:
                    # The argument is required and thus this will raise an
                    # exception if absent
                    value = data[arg]
                else:
                    # Set the value to the default
                    value = default if arg not in data else data[arg]
            # Otherwise assume the arguments are in the default content type
            else:
                # The argument is required and thus this will raise an
                # exception if absent
                if default is None:
                    value = self.get_argument(arg)
                else:
                    value = self.get_argument(arg, default)
        except Exception as e:
            response = str(e).strip()
            log.error(response)
            # 400 Bad Request: The server could not understand the request due
            # to invalid syntax.
            # The assumption is that if a function uses `getarg()` to get a
            # required parameter, then the request must be a bad request if
            # this exception occurs.
            self.send_response(response, http_status_code=global_vars.HTTP_BAD_REQUEST, return_json=False)
            raise e
        return value

    # The datetime type is not JSON serializable, so convert to string
    def json_converter(self, o):
        if isinstance(o, datetime):
            return str(o)

    def send_response(self, data, http_status_code=global_vars.HTTP_OK, return_json=True, indent=None):
        if return_json:
            if indent:
                self.write(json.dumps(data, indent=indent, default=self.json_converter))
            else:
                self.write(json.dumps(data, default=self.json_converter))
            self.set_header("Content-Type", "application/json")
        else:
            self.write(data)
        self.set_status(http_status_code)


def valid_job_id(job_id):
    # For testing purposes, treat the string 'invalid_job_id' as an invalid
    # job_id
    return isinstance(job_id, str) and len(job_id) > 0


def construct_job_object(job_info):
    job = {}
    try:
        creationTime = job_info["creation_time"]
        startTime = job_info["status"]["start_time"]
        endTime = job_info["status"]["completion_time"]
        destructionTime = None  # TODO: Should we track deletion time?
        try:
            executionDuration = (endTime - startTime).total_seconds()
        except Exception:
            executionDuration = None
        try:
            message = job_info["message"]
        except KeyError:
            message = ""
        # Determine job phase. For definitions see:
        #     https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#ExecutionPhase
        job_phase = "unknown"
        if creationTime:
            job_phase = "pending"
        if startTime:
            job_phase = "queued"
            if job_info["status"]["active"]:
                job_phase = "executing"
            if job_info["status"]["failed"]:
                job_phase = "error"
        if endTime:
            job_phase = "completed"
            if not job_info["status"]["succeeded"] or job_info["status"]["failed"]:
                job_phase = "error"

        results = []
        try:
            for idx, filepath in enumerate(job_info["output_files"]):
                results.append(
                    {
                        "id": idx,
                        "uri": filepath,
                        # 'mime-type': 'image/fits',
                        # 'size': '3000960',
                    }
                )
        except Exception as e:
            log.error(str(e))
            results = []
        # See job_schema.xml
        #   https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#jobobj
        job = {
            "jobId": job_info["job_id"],
            "runId": job_info["run_id"],
            "ownerId": "",  # TODO: Track identity of job owner
            "phase": job_phase,
            "creationTime": creationTime,
            "startTime": startTime,
            "endTime": endTime,
            "executionDuration": executionDuration,
            "destruction": destructionTime,
            "parameters": {
                "command": job_info["command"],
                "environment": job_info["environment"],
            },
            "results": results,
            "errorSummary": {
                "message": message,
            },
            "jobInfo": {},
        }
    except Exception as e:
        log.error(str(e))
    return job


class JobHandler(BaseHandler):
    def put(self):
        try:
            # Command that the job container will execute
            command = self.getarg("command")  # required
            # Valid run_id value follows the Kubernetes label value
            # constraints:
            #   - must be 63 characters or less (cannot be empty),
            #   - must begin and end with an alphanumeric character
            #     ([a-z0-9A-Z]),
            #   - could contain dashes (-), underscores (_), dots (.), and
            #     alphanumerics between.
            # See also:
            #   - https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#runId
            #   - https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#syntax-and-character-set
            run_id = self.getarg("run_id", default="")  # optional
            if run_id and (
                not isinstance(run_id, str)
                or run_id != re.sub(r"[^-._a-zA-Z0-9]", "", run_id)
                or not re.match(r"[a-zA-Z0-9]", run_id)
            ):
                self.send_response(
                    "Invalid run_id. Must be 63 characters or less and begin with alphanumeric character and "
                    "contain only dashes (-), underscores (_), dots (.), and alphanumerics between.",
                    http_status_code=global_vars.HTTP_BAD_REQUEST,
                    return_json=False,
                )
                self.finish()
                return
            # environment is a list of environment variable names and values
            # like [{'name': 'env1', 'value': 'val1'}]
            environment = self.getarg("environment", default=[])  # optional
            # Number of parallel job containers to run. The containers will
            # execute identical code. Coordination is the responsibility of the
            # job owner.
            replicas = self.getarg("replicas", default=1)  # optional
            # The URL of the git repo to clone
            url = self.getarg("url", default="")  # optional
            # The git reference (branch name or commit hash) to be checked out
            # after cloning the git repo
            commit_ref = self.getarg("commit_ref", default="")  # optional
        except Exception as e:
            self.send_response(str(e), http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False)
            self.finish()
            return
        response = kubejob.create_job(
            command=command,
            run_id=run_id,
            replicas=replicas,
            environment=environment,
            url=url,
            commit_ref=commit_ref,
        )
        # log.debug(response)
        if response["status"] != global_vars.STATUS_OK:
            self.send_response(
                response["message"], http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False
            )
            self.finish()
            return
        try:
            timeout = 30
            while timeout > 0:
                results = kubejob.list_jobs(
                    job_id=response["job_id"],
                )
                if results["jobs"]:
                    job = construct_job_object(results["jobs"][0])
                    self.send_response(job, indent=2)
                    self.finish()
                    return
                else:
                    timeout -= 1
                    time.sleep(0.300)
            self.send_response(
                "Job creation timed out.", http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False
            )
            self.finish()
            return
        except Exception as e:
            self.send_response(str(e), http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False)
            self.finish()
            return

    def get(self, job_id=None, property=None):
        # See https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#resourceuri
        valid_properties = {
            "phase": "phase",
            "results": "results",
            "parameters": "parameters",
        }
        response = {}
        # If no job_id is included in the request URL, return a list of jobs.
        # See:
        # UWS Schema: https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#UWSSchema
        if not job_id:
            phase = self.getarg("phase", default="")  # optional
            if not phase or phase in global_vars.VALID_JOB_STATUSES:
                results = kubejob.list_jobs()
                if results["status"] != global_vars.STATUS_OK:
                    self.send_response(
                        results["message"], http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False
                    )
                    self.finish()
                    return
            else:
                response = f"Valid job categories are: {global_vars.VALID_JOB_STATUSES}"
                self.send_response(response, http_status_code=global_vars.HTTP_BAD_REQUEST, return_json=False)
                self.finish()
                return
            # Construct the UWS-compatible list of job objects
            jobs = []
            for job_info in results["jobs"]:
                job = construct_job_object(job_info)
                if not phase or job["phase"] == phase:
                    jobs.append(job)
            self.send_response(jobs, indent=2)
            self.finish()
            return
        # If a job_id is provided but it is invalid, then the request is
        # malformed:
        if not valid_job_id(job_id):
            self.send_response("Invalid job ID.", http_status_code=global_vars.HTTP_BAD_REQUEST, indent=2)
            self.finish()
            return
        # If a property is provided but it is invalid, then the request is
        # malformed:
        elif isinstance(property, str) and property not in valid_properties:
            key_string = ", ".join(list(valid_properties.keys()))
            self.send_response(
                f"Invalid job property requested. Supported properties are {key_string}",
                http_status_code=global_vars.HTTP_BAD_REQUEST,
                indent=2,
            )
            self.finish()
            return
        else:
            try:
                results = kubejob.list_jobs(
                    job_id=job_id,
                )
                if results["status"] != global_vars.STATUS_OK:
                    self.send_response(
                        results["message"], http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False
                    )
                    self.finish()
                    return
                if not results["jobs"]:
                    self.send_response(results["message"], http_status_code=global_vars.HTTP_NOT_FOUND)
                    self.finish()
                    return
                job = construct_job_object(results["jobs"][0])

                # If a specific job property was requested using an API
                # endpoint of the form `/job/[job_id]/[property]]`, return that
                # property only.
                if property in valid_properties.keys():
                    self.send_response(job[valid_properties[property]], indent=2)
                else:
                    self.send_response(job, indent=2)
                self.finish()
                return
            except Exception as e:
                response = str(e).strip()
                log.error(response)
                self.send_response(response, http_status_code=global_vars.HTTP_SERVER_ERROR, indent=2)
                self.finish()
                return

    def delete(self, job_id):
        response = kubejob.delete_job(
            job_id=job_id,
        )
        log.debug(response)
        if response["status"] == global_vars.STATUS_ERROR:
            self.send_response(
                response["message"], http_status_code=global_vars.HTTP_SERVER_ERROR, return_json=False
            )
        elif isinstance(response["code"], int) and response["code"] != global_vars.HTTP_OK:
            self.send_response(response["message"], http_status_code=response["code"], return_json=False)
        else:
            self.send_response(response, indent=2)
        self.finish()
        return


class ResultFileHandler(BaseHandler):
    def get(self, job_id=None, result_id=None):
        try:
            # If a job_id is provided but it is invalid, then the request is
            # malformed:
            if not valid_job_id(job_id):
                self.send_response("Invalid job ID.", http_status_code=global_vars.HTTP_BAD_REQUEST, indent=2)
                self.finish()
                return
            # If a result_id is not provided, then the request is malformed:
            if not result_id:
                self.send_response(
                    "Invalid result ID.", http_status_code=global_vars.HTTP_BAD_REQUEST, indent=2
                )
                self.finish()
                return
            try:
                result_idx = int(result_id)
                job_files = kubejob.list_job_output_files(job_id)
                file_path = job_files[result_idx]
            except Exception:
                self.send_response(
                    "Result file not found.", http_status_code=global_vars.HTTP_NOT_FOUND, return_json=False
                )
                self.finish()
                return
            if not os.path.isfile(file_path):
                self.send_response(
                    "Result file not found.", http_status_code=global_vars.HTTP_NOT_FOUND, return_json=False
                )
                self.finish()
                return
            # TODO: Consider applying "application/octet-stream" universally
            # given the error rate with the guess_type() function
            content_type, _ = guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"
            self.add_header("Content-Type", content_type)
            with open(file_path, "rb") as source_file:
                self.send_response(source_file.read(), return_json=False)
                self.finish()
                return

        except Exception as e:
            response = str(e).strip()
            log.error(response)
            self.send_response(response, http_status_code=global_vars.HTTP_SERVER_ERROR, indent=2)
            self.finish()
            return


def make_app(base_path=""):
    settings = {"debug": True}
    return tornado.web.Application(
        [
            (rf"{base_path}/job/result/(.*)/(.*)", ResultFileHandler),
            (rf"{base_path}/job/(.*)/(.*)", JobHandler),
            (rf"{base_path}/job/(.*)", JobHandler),
            (rf"{base_path}/job", JobHandler),
        ],
        **settings,
    )


if __name__ == "__main__":
    base_path = config["server"]["basePath"]
    port = config["server"]["port"]
    app = make_app(base_path=base_path)
    app.listen(int(port))
    service = config["server"]["service"]
    protocol = config["server"]["protocol"]
    log.info(f"""UWS API server online at {protocol}://{service}:{port}{base_path}""")
    tornado.ioloop.IOLoop.current().start()
