#!/bin/bash -e

# Load the software and environment configuration
source "/opt/lsst/software/stack/loadLSST.bash"
setup lsst_distrib
export PYTHONPATH=$PYTHONPATH:/usr/lib64/python3.6/site-packages

export OUTPUT_COLLECTION="u/ocps/$JOB_ID"
export PIPELINE_YAML="$PIPE_TASKS_DIR/pipelines/DRP.yaml#processCcd"

pipetask run -p ${PIPELINE_YAML} \
    -C "${CONFIG_OVERRIDES}" \
    -b "${BUTLER_CONFIG}" \
    -i "${INPUT_COLLECTIONS}" \
    -o "${OUTPUT_COLLECTION}" \
    --output-run "${OUTPUT_COLLECTION}/run" \
    -d "${DATA_QUERY}"
    
export paths=$(butler query-datasets --collections $OUTPUT_COLLECTION/run $BUTLER_CONFIG "metricvalue_*" | sed -e 's/.*file:([^ ]*) .*/\1/')

cp $paths $JOB_OUTPUT_DIR