import os
import yaml

# Define all global constants

global STATUS_ERROR
global STATUS_OK
global CONDOR_JOB_STATES
global VALID_JOB_STATUSES

global HTTP_BAD_REQUEST
global HTTP_UNAUTHORIZED
global HTTP_NOT_FOUND

global API_PORT
global API_BASEPATH
global API_DOMAIN
global API_PROTOCOL

# Define all global constants
STATUS_OK = 'ok'
STATUS_ERROR = 'error'

# UWS Schema: https://www.ivoa.net/documents/UWS/20161024/REC-UWS-1.1-20161024.html#UWSSchema
VALID_JOB_STATUSES = [
    'pending',
    'queued',
    'executing',
    'completed',
    'error',
    'unknown',
    'held',
    'suspended',
    'aborted',
]

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 403
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

# Load configuration file
with open('/etc/config/uws.yaml', "r") as conf_file:
    config = yaml.load(conf_file, Loader=yaml.FullLoader)

