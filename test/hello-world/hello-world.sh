#!/bin/bash
set -x

echo "Custom environment variable: ${CUSTOM_ENV_VAR}"
# List mounted volume contents
ls -lan "${PROJECT_PATH}"
ls -lan /repo
ls -lan /uws