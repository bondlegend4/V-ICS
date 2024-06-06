#!/bin/bash

source $(dirname $0)/scadalts-data/openplc.yaml

NAMESPACE=v-ics  # Adjust if needed

if [ $# -ne 1 ]; then
    echo "Usage: $0 <number_of_openplc_instances>"
    exit 1
fi

instances=$1
current_port=$START_PORT
current_node_port=$START_NODE_PORT

for i in $(seq 1 $instances); do
    name="openplc-instance$i"

    # Create a temporary YAML file
    tmpfile=$(mktemp)
    sed -e "s/# To be replaced/$name/g" \
        -e "s/# To be replaced/$NAMESPACE/g" \
        -e "s/# To be replaced/$current_port/g" \
        -e "s/# To be replaced/$current_node_port/g" \
        -e "s/# To be replaced/$OPENPLC_IMAGE/g" \
        $OPENPLC_YAML > $tmpfile

    # Apply the temporary YAML file
    kubectl apply -f $tmpfile

    # Clean up the temporary YAML file
    rm $tmpfile

    ((current_port++))
    ((current_node_port++))
done