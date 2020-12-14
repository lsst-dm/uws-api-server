# Define all global constants
STATUS_OK = 'ok'
STATUS_ERROR = 'error'
CONDOR_JOB_STATES = {
    1: 'idle',
    2: 'running',
    3: 'removed',
    4: 'completed',
    5: 'held',
    6: 'transferring_output',
    7: 'suspended',
}

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