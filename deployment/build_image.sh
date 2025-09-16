#!/bin/bash

# Script to build all Docker images for the services,
# locally (with --no-cache) and load them into the Minikube cluster.

set -e

# --- Argument Validation ---
if [ -z "$1" ]; then
    echo "Error: You must specify the path to the nodes configuration file (e.g., deployment/nodes_config.yaml)." >&2
    exit 1
fi

CONFIG_FILE="$1"

# --- Reading the Cluster Name from the YAML file ---
CLUSTER_NAME=$(python3 -c "
import yaml, sys
filename = sys.argv[1]
try:
    with open(filename, 'r') as f:
        config = yaml.safe_load(f)
        if config and isinstance(config, dict) and 'name' in config:
            print(config['name'])
        else:
            print(f\"Error: Key 'name' not found in {filename}\", file=sys.stderr)
            sys.exit(1)
except Exception as e:
    print(f\"Error reading {filename}: {e}\", file=sys.stderr)
    sys.exit(1)
" "$CONFIG_FILE")

if [ $? -ne 0 ] || [ -z "$CLUSTER_NAME" ]; then
    echo "Unable to read the cluster name from the YAML file. Check the error messages."
    exit 1
fi

echo "Cluster name read: $CLUSTER_NAME"
echo "-----------------------------------------------------"
echo "Building and loading images for cluster: $CLUSTER_NAME"
echo "-----------------------------------------------------"

# --- Helper Function to Build and Load ---
build_and_load() {
    local image_name="$1"
    local dockerfile_path="$2"
    local build_context="$3"

    echo ""
    echo ">>> Starting process for image: $image_name"
    echo "----------------------------------------------------"
    
    echo "1/2: Building image '$image_name' locally (with --no-cache)..."
    docker build -t "$image_name" -f "$dockerfile_path" "$build_context"
    
    echo "2/2: Loading image '$image_name' into Minikube cluster nodes '$CLUSTER_NAME'..."
    minikube -p "$CLUSTER_NAME" image load "$image_name"
    
    echo ">>> Process for image $image_name completed."
    echo "----------------------------------------------------"
}

# --- Build Images with the NEW NAMES ---

# LARGE FLAVOUR (formerly HIGH)
build_and_load "brewery-gateway:large"      "src/gateway/high/Dockerfile"      "src/gateway/high"
build_and_load "brewery-aggregator:large"   "src/aggregator/high/Dockerfile"   "src/aggregator/high"
build_and_load "brewery-data-gather:large"  "src/data-gather/high/Dockerfile"  "src/data-gather/high"
build_and_load "brewery-analyzer:large"     "src/analyzer/high/Dockerfile"     "src/analyzer/high"

# TINY FLAVOUR (formerly LOW)
build_and_load "brewery-gateway:tiny"       "src/gateway/low/Dockerfile"       "src/gateway/low"
build_and_load "brewery-aggregator:tiny"    "src/aggregator/low/Dockerfile"    "src/aggregator/low"
build_and_load "brewery-data-gather:tiny"   "src/data-gather/low/Dockerfile"   "src/data-gather/low"


echo ""
echo "-----------------------------------------------------"
echo "All builds for cluster $CLUSTER_NAME have been completed."
echo "The images are now available on all nodes."
echo "-----------------------------------------------------"
