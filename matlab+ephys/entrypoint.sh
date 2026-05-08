#!/bin/bash

# Copyright 2021-2024 The MathWorks, Inc.

set -e

# set the umask for correct permissions 
umask 002

# Source the utilities
if [ -f /usr/local/bin/utils.sh ]; then
    . /usr/local/bin/utils.sh
else
    echo "Error: utils.sh not found"
    exit 1
fi

# Initialize variables
modes=0
CUSTOM_COMMAND=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
    -help)
        HELP=true
        modes=$((modes + 1))
        ;;
    -vnc | -shell)
        VNC=true
        modes=$((modes + 1))
        ;;
    -browser)
        BROWSER=true
        modes=$((modes + 1))
        ;;
    *)
        CUSTOM_COMMAND="${CUSTOM_COMMAND} $(build_cmd "$1")"
        ;;
    esac
    shift
done

# If no mode specified, default to browser mode
if [ "${modes}" -eq 0 ]; then
    BROWSER=true
fi

# Validate input and setup environment
validateInput
checkLicensing
checkSharedMemorySpace
checkEnvironmentVariables

# If help, vnc, or shell mode, use the original run script behavior
if [ "${HELP}" = true ] || [ "${VNC}" = true ]; then
    exec /usr/local/bin/run.sh "$@"
fi

# For browser mode (default), run supervisord
if [ "${BROWSER}" = true ]; then
    # Ensure MATLAB directories exist
    mkdir -p ~/Documents/MATLAB
    cd ~/Documents/MATLAB
    
    # Start supervisord
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi

# Fallback to original MATLAB execution
cd ~/Documents/MATLAB || exit 1
eval exec "matlab ${ARGLIST} ${CUSTOM_COMMAND}"(base)