#!/bin/bash

# Assert the number of arguments
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <simulation_path>"
    exit 1
fi


simulation_path=$1

python3 sumo_config/gen_routes.py $simulation_path

echo "Done! New routes generated in $simulation_path"
