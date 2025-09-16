#!/bin/bash

# Master script to automate the entire process:
# 1. Minikube cluster setup.
# 2. Kubernetes manifest generation.
# Intermediate step: ballast application on nodes
# 3. Docker image build.
# 4. Application deployment.
# 5. Modification of pod resources according to configuration.

# Stop execution if any command fails.
set -e

# --- Configuration ---
DEPLOYMENT_DIR="deployment"
NAMESPACE="brewery"
NODES_CONFIG="$DEPLOYMENT_DIR/nodes_config.yaml"
MANIFEST_FILE="$DEPLOYMENT_DIR/k8s/deployment-$NAMESPACE.yaml"
RESOURCE_CONFIG_FILE="$DEPLOYMENT_DIR/modificare_risorse_pods/pods_config_resource.yaml"

# --- Script Start ---
echo "--- Starting build and setup process ---"

# --- Step 1: Minikube cluster setup ---
echo ""
echo "--- Step 1: Setting up Minikube cluster with setup_nodes.py ---"
if [ -f "$DEPLOYMENT_DIR/setup_nodes.py" ]; then
    python3 "$DEPLOYMENT_DIR/setup_nodes.py" --config "$NODES_CONFIG"
    echo "setup_nodes.py executed successfully."
else
    echo "Error: $DEPLOYMENT_DIR/setup_nodes.py not found."
    exit 1
fi

# --- Step 2: Kubernetes manifest generation ---
echo ""
echo "--- Step 2: Generating Kubernetes manifest with build_manifest.py ---"
if [ -f "$DEPLOYMENT_DIR/build_manifest.py" ]; then
    python3 "$DEPLOYMENT_DIR/build_manifest.py" --namespace "$NAMESPACE"
    echo "build_manifest.py executed successfully."
else
    echo "Error: $DEPLOYMENT_DIR/build_manifest.py not found."
    exit 1
fi

# --- Step 3: Docker image build ---
echo ""
echo "--- Step 3: Building Docker images with build_image.sh ---"
if [ -f "$DEPLOYMENT_DIR/build_image.sh" ]; then
    # Execute the build_image.sh script, passing it the node configuration file.
    bash "$DEPLOYMENT_DIR/build_image.sh" "$NODES_CONFIG"
    echo "build_image.sh executed successfully."
else
    echo "Error: $DEPLOYMENT_DIR/build_image.sh not found."
    exit 1
fi

# --- Step 4: Application deployment on Kubernetes ---
echo ""
echo "--- Step 4: Deploying the application with kubectl apply ---"
if [ -f "$MANIFEST_FILE" ]; then
    kubectl apply -f "$MANIFEST_FILE"
    echo "Application deployed. Waiting for services to stabilize..."
else
    echo "Error: Manifest file $MANIFEST_FILE not found. Make sure build_manifest.py was executed correctly."
    exit 1
fi

# --- Step 5: Waiting for deployments to be ready ---
echo ""
echo "--- Step 5: Waiting for all deployments in namespace '$NAMESPACE' to be ready ---"
echo "Waiting 15 seconds before checking rollouts to give the cluster time to register deployments..."
sleep 15
DEPLOYMENTS=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

if [ -z "$DEPLOYMENTS" ]; then
    echo "Warning: No deployments found in namespace '$NAMESPACE'. Skipping rollout wait."
else
    for DEPLOYMENT in $DEPLOYMENTS; do
        echo "Waiting for rollout of deployment: $DEPLOYMENT..."
        # Wait until each deployment finishes updating.
        kubectl rollout status deployment "$DEPLOYMENT" -n "$NAMESPACE" --timeout=5m
    done
    echo "All deployments are ready."
fi

# --- Step 6 (NEW): Pod resource modification ---
echo ""
echo "--- Step 6: Modifying pod resources with modify_resource.py ---"
if [ -f "$DEPLOYMENT_DIR/modificare_risorse_pods/modify_resource.py" ]; then
    python3 "$DEPLOYMENT_DIR/modificare_risorse_pods/modify_resource.py" --config "$RESOURCE_CONFIG_FILE"
    echo "modify_resource.py executed successfully."
else
    echo "Error: $DEPLOYMENT_DIR/modificare_risorse_pods/modify_resource.py not found."
    exit 1
fi

echo ""
echo "--- Process completed successfully! ---"
