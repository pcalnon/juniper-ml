#!/usr/bin/env bash

# conda_install_dir="/path/to/conda/install/dir"
conda_install_dir="/opt/miniforge3"
conda_activate_dir="${conda_install_dir}/etc/profile.d"
conda_activate_script="${conda_activate_dir}/conda.sh"

# Define function to list currently active conda env
function get_active_conda_env() {
    # List active conda env name (indicated by "*") after ignoring commented lines and parsing env name using awk
    conda env list | grep -v -e "^\ *#.*$" | grep "\*" | awk -F " " '{print $1;}'
}

# Get and Display original conda env
active_conda_env="$(get_active_conda_env)"
echo "Initially Active Conda Env: \"${active_conda_env}\""


####################################################################
#
# Run script code, as needed, BEFORE source code compilation 
#
####################################################################


source "${conda_activate_script}"
conda deactivate
echo "Deactivated Conda Env: \"$(get_active_conda_env)\""

####################################################################
#
# run source code compilation here, using default Ubuntu env
#
####################################################################

source "${conda_activate_script}"
conda activate "${active_conda_env}"

# Display New conda env
echo "Final Active Conda Env: \"$(get_active_conda_env)\""


####################################################################
#
# Run script code, as needed, AFTER source code compilation 
#
####################################################################

