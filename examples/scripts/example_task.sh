#!/bin/bash
#
# Example task script for BashScriptRunner.
#
# This script is invoked whenever a Dripline ``on_set`` message is sent
# to the BashScriptRunner endpoint.  The incoming value is available as
# the environment variable ``$DRIPLINE_VALUE`` (JSON-encoded).
#
# Mount this script (or your own) into the container at deploy time,
# e.g. via a Docker Swarm volume bind-mount:
#
#   volumes:
#     - /host/path/my_task.sh:/scripts/example_task.sh:ro
#

set -euo pipefail

echo "=== BashScriptRunner example task ==="
echo "Received DRIPLINE_VALUE: ${DRIPLINE_VALUE:-<empty>}"
echo "Script path: $0"
echo "Current time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=== Done ==="
